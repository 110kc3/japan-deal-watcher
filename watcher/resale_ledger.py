"""Purchase-to-resale ledger and owner financial tracking engine.

Tracks the entire physical lifecycle of imported goods from purchase to Polish resale:
planned -> bought -> in_warehouse -> shipped -> received_tested -> listed -> sold / returned.

Core rule: NO "realized" profit before confirmed settlement (status == 'sold' with actual settlement).
Unsold units remain in capital-at-risk. Returns adjust totals.
"""

import csv
import io
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

from .config import (
    DEFAULT_JPY_PLN_RATE,
    RESALE_LEDGER_FILE,
    RESALE_LEDGER_CSV_FILE
)
from .storage import atomic_write_json, read_json_safe

logger = logging.getLogger(__name__)

LIFECYCLE_STAGES = (
    "planned",
    "bought",
    "in_warehouse",
    "shipped",
    "received_tested",
    "listed",
    "sold",
    "returned"
)

STAGE_PROGRESSION: Dict[str, Sequence[str]] = {
    "planned": ("bought", "returned"),
    "bought": ("in_warehouse", "returned"),
    "in_warehouse": ("shipped", "returned"),
    "shipped": ("received_tested", "returned"),
    "received_tested": ("listed", "returned"),
    "listed": ("sold", "returned"),
    "sold": ("returned",),
    "returned": ("listed", "received_tested")
}

CSV_FIELDNAMES = [
    "item_id",
    "model",
    "category_id",
    "purchase_date",
    "purchase_price_jpy",
    "fx_rate_jpy_pln",
    "actual_fees_pln",
    "actual_freight_pln",
    "actual_customs_vat_pln",
    "landed_cost_pln",
    "testing_repair_cost_pln",
    "handling_hours",
    "listing_channel",
    "sale_price_pln",
    "selling_fees_pln",
    "shipping_packing_cost_pln",
    "net_settlement_pln",
    "refund_amount_pln",
    "realized_profit_pln",
    "realized_roi_pct",
    "status",
    "notes"
]

class ResaleLedger:
    """Purchase-to-resale lifecycle and financial ledger."""

    def __init__(self, filepath: Optional[Union[Path, str]] = None):
        self.filepath = Path(filepath or RESALE_LEDGER_FILE)
        self.data: Dict[str, Any] = self._load()

    def _default_data(self) -> Dict[str, Any]:
        now_iso = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ")
        return {
            "metadata": {
                "version": "1.0",
                "created_at": now_iso,
                "last_updated": now_iso,
                "total_items": 0
            },
            "items": {}
        }

    def _load(self) -> Dict[str, Any]:
        data = read_json_safe(self.filepath, default=self._default_data)
        if not isinstance(data, dict) or "items" not in data:
            data = self._default_data()
        data.setdefault("metadata", {})
        data.setdefault("items", {})
        return data

    def save(self) -> None:
        """Atomically saves the ledger to disk."""
        now_iso = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ")
        self.data["metadata"]["last_updated"] = now_iso
        self.data["metadata"]["total_items"] = len(self.data["items"])
        atomic_write_json(self.filepath, self.data)

    def _calculate_financials(self, item: Dict[str, Any]) -> None:
        """
        Calculates landed cost, net settlement, and realized profit/ROI.
        Enforces: NO realized profit unless status == 'sold' with confirmed settlement.
        """
        price_jpy = float(item.get("purchase_price_jpy") or 0.0)
        fx_rate = float(item.get("fx_rate_jpy_pln") or DEFAULT_JPY_PLN_RATE)
        base_pln = price_jpy * fx_rate
        fees_pln = float(item.get("actual_fees_pln") or 0.0)
        freight_pln = float(item.get("actual_freight_pln") or 0.0)
        vat_pln = float(item.get("actual_customs_vat_pln") or 0.0)

        landed = float(item.get("landed_cost_pln") or 0.0)
        if landed <= 0.0 and (price_jpy > 0 or fees_pln > 0 or freight_pln > 0 or vat_pln > 0):
            landed = round(base_pln + fees_pln + freight_pln + vat_pln, 2)
            item["landed_cost_pln"] = landed
        else:
            item["landed_cost_pln"] = round(landed, 2)

        repair_cost = round(float(item.get("testing_repair_cost_pln") or 0.0), 2)
        item["testing_repair_cost_pln"] = repair_cost
        total_invested = round(landed + repair_cost, 2)

        sale_price = item.get("sale_price_pln")
        selling_fees = round(float(item.get("selling_fees_pln") or 0.0), 2)
        shipping_cost = round(float(item.get("shipping_packing_cost_pln") or 0.0), 2)
        refund_amount = round(float(item.get("refund_amount_pln") or 0.0), 2)

        item["selling_fees_pln"] = selling_fees
        item["shipping_packing_cost_pln"] = shipping_cost
        item["refund_amount_pln"] = refund_amount

        net_settlement = item.get("net_settlement_pln")
        if sale_price is not None:
            sale_price = round(float(sale_price), 2)
            item["sale_price_pln"] = sale_price
            if net_settlement is None:
                net_settlement = round(sale_price - selling_fees - shipping_cost, 2)
                item["net_settlement_pln"] = net_settlement
            else:
                item["net_settlement_pln"] = round(float(net_settlement), 2)
        elif net_settlement is not None:
            item["net_settlement_pln"] = round(float(net_settlement), 2)

        status = item.get("status")
        if status == "sold" and item.get("net_settlement_pln") is not None:
            settled = float(item["net_settlement_pln"])
            profit = round(settled - refund_amount - total_invested, 2)
            item["realized_profit_pln"] = profit
            if total_invested > 0:
                item["realized_roi_pct"] = round((profit / total_invested) * 100.0, 2)
            else:
                item["realized_roi_pct"] = 0.0
        else:
            item["realized_profit_pln"] = None
            item["realized_roi_pct"] = None

    def add_item(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adds a new tracked item into the ledger.
        """
        item_id = str(item_data.get("item_id") or "").strip()
        if not item_id:
            raise ValueError("item_id is required and cannot be empty")

        status = item_data.get("status", "planned")
        if status not in LIFECYCLE_STAGES:
            raise ValueError(f"Invalid status '{status}'. Must be one of {LIFECYCLE_STAGES}")

        now_iso = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ")
        record: Dict[str, Any] = {
            "item_id": item_id,
            "model": str(item_data.get("model") or ""),
            "category_id": str(item_data.get("category_id") or "general"),
            "purchase_date": item_data.get("purchase_date"),
            "purchase_price_jpy": float(item_data.get("purchase_price_jpy") or 0.0),
            "fx_rate_jpy_pln": float(item_data.get("fx_rate_jpy_pln") or DEFAULT_JPY_PLN_RATE),
            "actual_fees_pln": float(item_data.get("actual_fees_pln") or 0.0),
            "actual_freight_pln": float(item_data.get("actual_freight_pln") or 0.0),
            "actual_customs_vat_pln": float(item_data.get("actual_customs_vat_pln") or 0.0),
            "landed_cost_pln": float(item_data.get("landed_cost_pln") or 0.0),
            "testing_repair_cost_pln": float(item_data.get("testing_repair_cost_pln") or 0.0),
            "handling_hours": float(item_data.get("handling_hours") or 0.0),
            "listing_channel": item_data.get("listing_channel"),
            "sale_price_pln": item_data.get("sale_price_pln"),
            "selling_fees_pln": float(item_data.get("selling_fees_pln") or 0.0),
            "shipping_packing_cost_pln": float(item_data.get("shipping_packing_cost_pln") or 0.0),
            "net_settlement_pln": item_data.get("net_settlement_pln"),
            "refund_amount_pln": float(item_data.get("refund_amount_pln") or 0.0),
            "status": status,
            "notes": str(item_data.get("notes") or ""),
            "sale_date": item_data.get("sale_date"),
            "settlement_date": item_data.get("settlement_date"),
            "created_at": now_iso,
            "updated_at": now_iso,
            "history": [
                {
                    "timestamp": now_iso,
                    "stage": status,
                    "note": "Item entered ledger"
                }
            ]
        }

        self._calculate_financials(record)
        self.data["items"][item_id] = record
        self.save()
        return record

    def get_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves item by id."""
        return self.data["items"].get(str(item_id))

    def update_item(self, item_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Updates fields on an existing item."""
        item = self.get_item(item_id)
        if not item:
            raise KeyError(f"Item '{item_id}' not found in resale ledger")

        now_iso = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ")
        for k, v in updates.items():
            if k not in ("item_id", "created_at", "history"):
                item[k] = v

        item["updated_at"] = now_iso
        self._calculate_financials(item)
        self.save()
        return item

    def transition_status(
        self,
        item_id: str,
        new_status: str,
        notes: Optional[str] = None,
        force: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Transitions an item to a new lifecycle stage.
        Validates transition progression unless force=True.
        """
        item = self.get_item(item_id)
        if not item:
            raise KeyError(f"Item '{item_id}' not found in resale ledger")

        if new_status not in LIFECYCLE_STAGES:
            raise ValueError(f"Invalid status '{new_status}'. Must be one of {LIFECYCLE_STAGES}")

        current_status = item["status"]
        if not force and current_status != new_status:
            allowed = STAGE_PROGRESSION.get(current_status, ())
            if new_status not in allowed:
                raise ValueError(
                    f"Invalid stage transition from '{current_status}' to '{new_status}'. "
                    f"Allowed next stages: {list(allowed)}"
                )

        now_iso = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ")
        item["status"] = new_status
        item["updated_at"] = now_iso

        if notes:
            existing_notes = item.get("notes", "")
            item["notes"] = f"{existing_notes}\n{notes}".strip() if existing_notes else notes

        for k, v in kwargs.items():
            if k not in ("item_id", "created_at", "history"):
                item[k] = v

        item.setdefault("history", []).append({
            "timestamp": now_iso,
            "from_stage": current_status,
            "to_stage": new_status,
            "note": notes or f"Transitioned to {new_status}"
        })

        self._calculate_financials(item)
        self.save()
        return item

    def record_settlement(
        self,
        item_id: str,
        sale_price_pln: float,
        selling_fees_pln: float = 0.0,
        shipping_packing_cost_pln: float = 0.0,
        net_settlement_pln: Optional[float] = None,
        sale_date: Optional[str] = None,
        settlement_date: Optional[str] = None,
        listing_channel: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Records the confirmed Polish market sale and payout settlement.
        Transitions the item to 'sold' and locks in realized profit.
        """
        item = self.get_item(item_id)
        if not item:
            raise KeyError(f"Item '{item_id}' not found in resale ledger")

        now_date = datetime.utcnow().strftime("%Y-%m-%d")
        effective_sale_date = sale_date or now_date
        effective_settlement_date = settlement_date or effective_sale_date

        calculated_net = net_settlement_pln
        if calculated_net is None:
            calculated_net = round(sale_price_pln - selling_fees_pln - shipping_packing_cost_pln, 2)

        updates: Dict[str, Any] = {
            "sale_price_pln": float(sale_price_pln),
            "selling_fees_pln": float(selling_fees_pln),
            "shipping_packing_cost_pln": float(shipping_packing_cost_pln),
            "net_settlement_pln": float(calculated_net),
            "sale_date": effective_sale_date,
            "settlement_date": effective_settlement_date,
        }
        if listing_channel:
            updates["listing_channel"] = listing_channel

        return self.transition_status(
            item_id=item_id,
            new_status="sold",
            notes=notes or f"Confirmed sale on {updates.get('listing_channel') or item.get('listing_channel') or 'market'}",
            force=False,
            **updates
        )

    def record_refund(
        self,
        item_id: str,
        refund_amount_pln: float,
        mark_returned: bool = True,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Records buyer refund. If mark_returned is True, transitions stage to 'returned'.
        Adjusts realized totals according to the core rule.
        """
        item = self.get_item(item_id)
        if not item:
            raise KeyError(f"Item '{item_id}' not found in resale ledger")

        existing_refund = float(item.get("refund_amount_pln") or 0.0)
        new_refund = round(existing_refund + float(refund_amount_pln), 2)
        item["refund_amount_pln"] = new_refund

        note_text = notes or f"Refund of {refund_amount_pln:.2f} PLN issued."
        if mark_returned:
            return self.transition_status(
                item_id=item_id,
                new_status="returned",
                notes=note_text,
                force=True,
                refund_amount_pln=new_refund
            )
        else:
            return self.update_item(
                item_id=item_id,
                updates={"refund_amount_pln": new_refund, "notes": f"{item.get('notes', '')}\n{note_text}".strip()}
            )

    def get_metrics(self) -> Dict[str, Any]:
        """
        Computes executive aggregated ledger metrics:
        - Capital tied up in unsold units (capital at risk)
        - Confirmed realized profit & ROI
        - Win rate (% profitable closed sales)
        - Average days to cash
        - Category and channel performance
        """
        items = list(self.data["items"].values())
        total_items = len(items)

        status_counts = {st: 0 for st in LIFECYCLE_STAGES}
        for it in items:
            st = it.get("status", "planned")
            if st in status_counts:
                status_counts[st] += 1

        capital_at_risk_stages = {"bought", "in_warehouse", "shipped", "received_tested", "listed", "returned"}
        capital_at_risk_pln = sum(
            float(it.get("landed_cost_pln") or 0.0) + float(it.get("testing_repair_cost_pln") or 0.0)
            for it in items if it.get("status") in capital_at_risk_stages
        )
        capital_planned_pln = sum(
            float(it.get("landed_cost_pln") or 0.0) + float(it.get("testing_repair_cost_pln") or 0.0)
            for it in items if it.get("status") == "planned"
        )

        sold_items = [it for it in items if it.get("status") == "sold" and it.get("realized_profit_pln") is not None]
        total_sales_count = len(sold_items)

        total_realized_profit_pln = sum(float(it["realized_profit_pln"]) for it in sold_items)
        total_invested_sold_pln = sum(
            float(it.get("landed_cost_pln") or 0.0) + float(it.get("testing_repair_cost_pln") or 0.0)
            for it in sold_items
        )
        total_net_settlement_pln = sum(float(it.get("net_settlement_pln") or 0.0) for it in sold_items)
        total_refunds_pln = sum(float(it.get("refund_amount_pln") or 0.0) for it in sold_items)

        overall_realized_roi_pct = (
            round((total_realized_profit_pln / total_invested_sold_pln) * 100.0, 2)
            if total_invested_sold_pln > 0 else 0.0
        )

        profitable_sales = [it for it in sold_items if float(it["realized_profit_pln"]) > 0]
        unprofitable_sales = [it for it in sold_items if float(it["realized_profit_pln"]) <= 0]
        win_rate_pct = (
            round((len(profitable_sales) / total_sales_count) * 100.0, 1)
            if total_sales_count > 0 else 0.0
        )

        days_list = []
        for it in sold_items:
            p_date_str = it.get("purchase_date")
            s_date_str = it.get("settlement_date") or it.get("sale_date")
            if p_date_str and s_date_str:
                try:
                    d_purchase = datetime.strptime(str(p_date_str)[:10], "%Y-%m-%d")
                    d_settle = datetime.strptime(str(s_date_str)[:10], "%Y-%m-%d")
                    diff_days = (d_settle - d_purchase).days
                    if diff_days >= 0:
                        days_list.append(diff_days)
                except Exception:
                    pass

        avg_days_to_cash = round(sum(days_list) / len(days_list), 1) if days_list else 0.0

        total_handling_hours = sum(float(it.get("handling_hours") or 0.0) for it in items)
        sold_handling_hours = sum(float(it.get("handling_hours") or 0.0) for it in sold_items)
        profit_per_hour_pln = (
            round(total_realized_profit_pln / sold_handling_hours, 2)
            if sold_handling_hours > 0 else 0.0
        )

        by_category: Dict[str, Dict[str, Any]] = {}
        for it in items:
            cat = it.get("category_id") or "general"
            cdata = by_category.setdefault(cat, {
                "total_items": 0,
                "sold_count": 0,
                "capital_at_risk_pln": 0.0,
                "realized_profit_pln": 0.0,
                "invested_sold_pln": 0.0
            })
            cdata["total_items"] += 1
            st = it.get("status")
            if st in capital_at_risk_stages:
                cdata["capital_at_risk_pln"] += (
                    float(it.get("landed_cost_pln") or 0.0) + float(it.get("testing_repair_cost_pln") or 0.0)
                )
            if st == "sold" and it.get("realized_profit_pln") is not None:
                cdata["sold_count"] += 1
                cdata["realized_profit_pln"] += float(it["realized_profit_pln"])
                cdata["invested_sold_pln"] += (
                    float(it.get("landed_cost_pln") or 0.0) + float(it.get("testing_repair_cost_pln") or 0.0)
                )

        for cat, cdata in by_category.items():
            cdata["capital_at_risk_pln"] = round(cdata["capital_at_risk_pln"], 2)
            cdata["realized_profit_pln"] = round(cdata["realized_profit_pln"], 2)
            cdata["invested_sold_pln"] = round(cdata["invested_sold_pln"], 2)
            cdata["realized_roi_pct"] = (
                round((cdata["realized_profit_pln"] / cdata["invested_sold_pln"]) * 100.0, 1)
                if cdata["invested_sold_pln"] > 0 else 0.0
            )

        by_channel: Dict[str, Dict[str, Any]] = {}
        for it in sold_items:
            chan = it.get("listing_channel") or "Unknown"
            chdata = by_channel.setdefault(chan, {
                "sales_count": 0,
                "realized_profit_pln": 0.0,
                "invested_sold_pln": 0.0
            })
            chdata["sales_count"] += 1
            chdata["realized_profit_pln"] += float(it["realized_profit_pln"])
            chdata["invested_sold_pln"] += (
                float(it.get("landed_cost_pln") or 0.0) + float(it.get("testing_repair_cost_pln") or 0.0)
            )

        for chan, chdata in by_channel.items():
            chdata["realized_profit_pln"] = round(chdata["realized_profit_pln"], 2)
            chdata["invested_sold_pln"] = round(chdata["invested_sold_pln"], 2)
            chdata["realized_roi_pct"] = (
                round((chdata["realized_profit_pln"] / chdata["invested_sold_pln"]) * 100.0, 1)
                if chdata["invested_sold_pln"] > 0 else 0.0
            )

        return {
            "total_items": total_items,
            "status_counts": status_counts,
            "capital_at_risk_pln": round(capital_at_risk_pln, 2),
            "capital_planned_pln": round(capital_planned_pln, 2),
            "total_sales_count": total_sales_count,
            "profitable_sales_count": len(profitable_sales),
            "unprofitable_sales_count": len(unprofitable_sales),
            "win_rate_pct": win_rate_pct,
            "total_realized_profit_pln": round(total_realized_profit_pln, 2),
            "total_net_settlement_pln": round(total_net_settlement_pln, 2),
            "total_invested_sold_pln": round(total_invested_sold_pln, 2),
            "total_refunds_pln": round(total_refunds_pln, 2),
            "overall_realized_roi_pct": overall_realized_roi_pct,
            "avg_days_to_cash": avg_days_to_cash,
            "total_handling_hours": round(total_handling_hours, 1),
            "profit_per_hour_pln": profit_per_hour_pln,
            "by_category": by_category,
            "by_channel": by_channel
        }

    def export_csv(self, filepath: Optional[Union[Path, str]] = None) -> Path:
        """
        Exports the entire ledger to a CSV backup file.
        """
        target = Path(filepath or RESALE_LEDGER_CSV_FILE)
        target.parent.mkdir(parents=True, exist_ok=True)

        items = list(self.data["items"].values())

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=CSV_FIELDNAMES, extrasaction="ignore")
        writer.writeheader()

        for it in items:
            row = {}
            for col in CSV_FIELDNAMES:
                val = it.get(col)
                row[col] = "" if val is None else val
            writer.writerow(row)

        content = output.getvalue()

        temp_file = target.parent / f".{target.name}.tmp.{int(datetime.utcnow().timestamp())}"
        try:
            with open(temp_file, "w", encoding="utf-8", newline="") as f:
                f.write(content)
                f.flush()
            temp_file.replace(target)
            return target
        except Exception:
            if temp_file.exists():
                temp_file.unlink()
            raise

    def export_json(self, filepath: Optional[Union[Path, str]] = None) -> Path:
        """
        Exports private backup JSON including metadata, items, and current metrics.
        """
        target = Path(filepath or self.filepath)
        export_payload = {
            "metadata": self.data.get("metadata", {}),
            "metrics": self.get_metrics(),
            "items": self.data.get("items", {})
        }
        return atomic_write_json(target, export_payload)
