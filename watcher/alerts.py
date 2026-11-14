"""Selective Discovery and Alerts Engine (Task 5, Choice 5, Fix F13).

Evaluates candidate listings against hard eligibility gates:
1. Identity: valid listing ID, non-empty model, non-expired status.
2. Price caps: camera price cap (<=100 PLN), lens price cap (<=100 PLN).
3. Defects & traps: exclusion of defect keywords, shipping traps (Chakubarai), and empty box/manual traps.
4. Logistics & battery limits: IATA lithium battery restrictions (<= 2 Li-ion).
5. Profitability & hurdle rate: minimum ROI (default 25%) and minimum net margin (default 40 PLN).

Emits alerts for:
a) Newly qualified opportunities (passed all gates, high confidence).
b) Price drops on tracked items.

Deduplicates alerts so the same listing ID is not alerted multiple times for the same price.
Persists alerts to data/alerts_history.json.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Set

from .config import (
    ALERTS_HISTORY_FILE,
    DEFAULT_JPY_PLN_RATE,
    DEFAULT_EUR_PLN_RATE,
    MAX_LI_ION_PER_PARCEL
)
from .costs import calculate_landed_cost
from .consolidation import resolve_item_battery_count
from .checks import (
    check_defects,
    check_shipping_trap,
    check_camera_price_cap,
    check_lens_price_cap,
    TRAP_KEYWORDS
)

logger = logging.getLogger(__name__)

class AlertsEngine:
    """
    Selective discovery and alerts engine for Japan Deal Watcher.
    Enforces strict buying gates and manages alert deduplication and persistence.
    """

    def __init__(
        self,
        alerts_file: Optional[Path] = None,
        min_roi: float = 25.0,
        min_margin_pln: float = 40.0,
        rate_jpy: float = DEFAULT_JPY_PLN_RATE,
        rate_eur: float = DEFAULT_EUR_PLN_RATE
    ):
        self.alerts_file = Path(alerts_file or ALERTS_HISTORY_FILE)
        self.min_roi = float(min_roi)
        self.min_margin_pln = float(min_margin_pln)
        self.rate_jpy = float(rate_jpy)
        self.rate_eur = float(rate_eur)
        self._history = self._load_history()

    def _load_history(self) -> Dict[str, Any]:
        """Loads alerts history from disk or initializes empty state."""
        if self.alerts_file.exists():
            try:
                with open(self.alerts_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and "alerts" in data and "alerted_signatures" in data:
                        return data
            except Exception as e:
                logger.warning(f"Could not load alerts history from {self.alerts_file}: {e}. Starting fresh.")

        return {
            "version": "1.0",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "total_alerts": 0,
            "alerted_signatures": {},
            "alerts": []
        }

    def _save_history(self) -> None:
        """Saves alerts history to disk."""
        self.alerts_file.parent.mkdir(parents=True, exist_ok=True)
        self._history["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._history["total_alerts"] = len(self._history["alerts"])
        with open(self.alerts_file, "w", encoding="utf-8") as f:
            json.dump(self._history, f, indent=2, ensure_ascii=False)

    def evaluate_gates(self, deal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates a candidate deal against all hard eligibility gates.
        Returns detailed gate report.
        """
        passed_gates = []
        failed_gates = []
        failure_reasons = []

        deal_id = str(deal.get("id") or "").strip()
        model = str(deal.get("model") or deal.get("name") or "").strip()
        price_jpy = float(deal.get("price_jpy", deal.get("target_price_jpy", 0)))
        status = str(deal.get("status", "active")).lower()

        if not deal_id or len(model) < 2 or price_jpy <= 0 or status in ["sold", "ended", "cancelled"]:
            failed_gates.append("identity")
            failure_reasons.append("Niepoprawne ID, pusta nazwa, zerowa cena lub zakończone ogłoszenie.")
        else:
            passed_gates.append("identity")

        cam_ok, cam_reason = check_camera_price_cap(deal, max_price_pln=100.0)
        lens_ok, lens_reason = check_lens_price_cap(deal, max_price_pln=100.0)
        if not cam_ok:
            failed_gates.append("price_caps")
            failure_reasons.append(cam_reason)
        elif not lens_ok:
            failed_gates.append("price_caps")
            failure_reasons.append(lens_reason)
        else:
            passed_gates.append("price_caps")

        text_corpus = " ".join([
            model,
            str(deal.get("custom_note", "")),
            str(deal.get("notes", "")),
            str(deal.get("search_query_jp", "")),
            str(deal.get("condition", ""))
        ])

        is_defect_free, defect_reason = check_defects(
            text_corpus,
            custom_note=str(deal.get("custom_note", "")),
            item_condition=str(deal.get("condition", ""))
        )
        if not is_defect_free:
            failed_gates.append("defects_and_traps")
            failure_reasons.append(defect_reason)
        else:
            is_shipping_ok, trap_reason = check_shipping_trap(text_corpus)
            if not is_shipping_ok:
                failed_gates.append("defects_and_traps")
                failure_reasons.append(trap_reason)
            else:
                passed_gates.append("defects_and_traps")

        battery_count = resolve_item_battery_count(deal)
        if battery_count > MAX_LI_ION_PER_PARCEL and not deal.get("dry_ship"):
            failed_gates.append("logistics")
            failure_reasons.append(
                f"Przekroczono limit IATA baterii litowych dla pojedynczej pozycji ({battery_count} > {MAX_LI_ION_PER_PARCEL})."
            )
        else:
            passed_gates.append("logistics")

        cat_id = deal.get("category_id")
        shipping_share = deal.get("shipping_share_pln")
        landed = calculate_landed_cost(
            price_jpy=price_jpy,
            category_id=cat_id,
            rate_jpy=self.rate_jpy,
            rate_eur=self.rate_eur,
            shipping_share_pln=shipping_share
        )
        landed_cost_pln = landed["landed_cost_pln"]
        est_pl_value = float(deal.get("est_pl_value", 0))

        net_margin_pln = round(est_pl_value - landed_cost_pln, 2)
        roi_pct = round((net_margin_pln / landed_cost_pln * 100.0), 1) if landed_cost_pln > 0 else 0.0

        if est_pl_value <= 0:
            failed_gates.append("profitability")
            failure_reasons.append("Brak polskiej wyceny rynkowej (est_pl_value = 0).")
        elif net_margin_pln < self.min_margin_pln:
            failed_gates.append("profitability")
            failure_reasons.append(
                f"Marża netto ({net_margin_pln:.2f} zł) poniżej progu minimalnego ({self.min_margin_pln:.2f} zł)."
            )
        elif roi_pct < self.min_roi:
            failed_gates.append("profitability")
            failure_reasons.append(
                f"ROI ({roi_pct:.1f}%) poniżej progu minimalnego ({self.min_roi:.1f}%)."
            )
        else:
            passed_gates.append("profitability")

        eligible = len(failed_gates) == 0

        return {
            "eligible": eligible,
            "deal_id": deal_id,
            "passed_gates": passed_gates,
            "failed_gates": failed_gates,
            "failure_reasons": failure_reasons,
            "economics": {
                "price_jpy": price_jpy,
                "landed_cost_pln": landed_cost_pln,
                "est_pl_value": est_pl_value,
                "net_margin_pln": net_margin_pln,
                "roi_pct": roi_pct
            }
        }

    def process_candidate(
        self,
        deal: Dict[str, Any],
        previous_price_jpy: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluates a candidate deal.
        If it qualifies, emits an alert of type 'new_opportunity' or 'price_drop'.
        Deduplicates against previous alerts.
        """
        gate_res = self.evaluate_gates(deal)
        if not gate_res["eligible"]:
            return None

        deal_id = gate_res["deal_id"]
        econ = gate_res["economics"]
        current_price_jpy = econ["price_jpy"]

        signatures = self._history.setdefault("alerted_signatures", {})
        existing_sig = signatures.get(deal_id)

        alert_type = None
        price_drop_jpy = 0.0

        if existing_sig is None:
            if previous_price_jpy is not None and current_price_jpy < previous_price_jpy:
                alert_type = "price_drop"
                price_drop_jpy = round(previous_price_jpy - current_price_jpy, 0)
            else:
                alert_type = "new_opportunity"
        else:
            last_price = existing_sig.get("last_price_jpy", current_price_jpy)
            if current_price_jpy < last_price:
                alert_type = "price_drop"
                price_drop_jpy = round(last_price - current_price_jpy, 0)
            else:
                return None

        now_iso = datetime.now(timezone.utc).isoformat()
        alert_id = f"alert_{deal_id}_{int(datetime.now(timezone.utc).timestamp())}"

        if alert_type == "price_drop":
            summary = (
                f"📉 SPADEK CENY: {deal.get('model')} staniał o {price_drop_jpy:,.0f} JPY! "
                f"Nowa cena: {current_price_jpy:,.0f} JPY. Marża netto w PL: +{econ['net_margin_pln']:.2f} zł (ROI: {econ['roi_pct']}%)."
            )
        else:
            summary = (
                f"⭐ NOWA OKAZJA: {deal.get('model')} przeszedł wszystkie bramki! "
                f"Cena: {current_price_jpy:,.0f} JPY. Marża netto w PL: +{econ['net_margin_pln']:.2f} zł (ROI: {econ['roi_pct']}%)."
            )

        alert = {
            "alert_id": alert_id,
            "listing_id": deal_id,
            "alert_type": alert_type,
            "created_at": now_iso,
            "model": deal.get("model") or deal.get("name"),
            "platform": deal.get("platform", "Mercari/Yahoo"),
            "current_price_jpy": current_price_jpy,
            "previous_price_jpy": previous_price_jpy if previous_price_jpy is not None else existing_sig.get("last_price_jpy") if existing_sig else None,
            "price_drop_jpy": price_drop_jpy,
            "est_pl_value": econ["est_pl_value"],
            "landed_cost_pln": econ["landed_cost_pln"],
            "net_margin_pln": econ["net_margin_pln"],
            "roi_pct": econ["roi_pct"],
            "confidence": "high",
            "gates_passed": gate_res["passed_gates"],
            "url": deal.get("url") or deal.get("link") or f"https://jp.mercari.com/item/{deal_id}",
            "summary": summary
        }

        signatures[deal_id] = {
            "last_alert_type": alert_type,
            "last_price_jpy": current_price_jpy,
            "alerted_at": now_iso
        }
        self._history["alerts"].append(alert)
        self._save_history()

        return alert

    def process_batch(
        self,
        deals: List[Dict[str, Any]],
        previous_prices: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        """Processes a list of deals and returns all newly emitted alerts."""
        previous_prices = previous_prices or {}
        new_alerts = []
        for d in deals:
            did = str(d.get("id", ""))
            prev_p = previous_prices.get(did)
            alert = self.process_candidate(d, previous_price_jpy=prev_p)
            if alert:
                new_alerts.append(alert)
        return new_alerts

    def get_alerts(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Returns persisted alerts ordered newest first."""
        alerts = list(reversed(self._history.get("alerts", [])))
        if limit is not None and limit > 0:
            return alerts[:limit]
        return alerts

    def get_alerted_ids(self) -> Set[str]:
        """Returns set of all listing IDs that have been alerted."""
        return set(self._history.get("alerted_signatures", {}).keys())

    def clear_history(self) -> None:
        """Clears all stored alerts history."""
        self._history = {
            "version": "1.0",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "total_alerts": 0,
            "alerted_signatures": {},
            "alerts": []
        }
        self._save_history()
