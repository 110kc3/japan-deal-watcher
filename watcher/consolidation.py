"""Consolidation, weight analysis, and 60-day packing timeline tracker."""

import re
import math
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional

from .config import (
    FREE_STORAGE_DAYS,
    CONSOLIDATION_START,
    MAX_LI_ION_PER_PARCEL,
    CATEGORY_ESTIMATED_WEIGHTS_G,
    DEFAULT_ITEM_WEIGHT_G,
    OUTER_BOX_BUFFER_WEIGHT_G,
    AVIA_MAX_WEIGHT_G,
    SHIPPING_METHODS,
    DEFAULT_JPY_PLN_RATE,
    DEFAULT_EUR_PLN_RATE,
    ZENMARKET_FEE_JPY,
    ZENMARKET_FEE_EUR,
    ZENMARKET_DEPOSIT_FEE_RATE,
    ZENMARKET_BATTERY_DISPOSAL_FEE_JPY,
    VAT_RATE
)


def resolve_item_weight(item: Dict[str, Any]) -> int:
    """Returns the estimated net weight of an item in grams."""
    if not item:
        return DEFAULT_ITEM_WEIGHT_G
    if "est_weight_g" in item and item["est_weight_g"] is not None:
        try:
            val = int(item["est_weight_g"])
            if val > 0:
                return val
        except (ValueError, TypeError):
            pass
    cat_id = item.get("category_id")
    if cat_id in CATEGORY_ESTIMATED_WEIGHTS_G:
        return CATEGORY_ESTIMATED_WEIGHTS_G[cat_id]

    name = (item.get("model") or item.get("name") or "").lower()
    if "3ds ll" in name or "new 3ds" in name:
        return 320
    if "ds lite" in name:
        return 220
    if "dsi ll" in name:
        return 315
    if "vita" in name:
        return 290
    if "psp" in name:
        return 260
    if "danshari" in name or "mystery" in name or "karton" in name or "zestaw" in name:
        return 1800
    return DEFAULT_ITEM_WEIGHT_G


def calculate_package_weight(
    items: List[Dict[str, Any]],
    box_buffer_g: int = OUTER_BOX_BUFFER_WEIGHT_G
) -> Dict[str, Any]:
    """
    Calculates net items weight, packaging box buffer, total parcel weight,
    and threshold status against AVIA Small Packet (2,000 g ceiling).
    """
    if not items:
        return {
            "item_count": 0,
            "net_weight_g": 0,
            "box_buffer_g": 0,
            "total_weight_g": 0,
            "total_weight_kg": 0.0,
            "is_avia_eligible": True,
            "avia_remaining_g": AVIA_MAX_WEIGHT_G,
            "avia_overweight_g": 0,
            "weight_pct_of_avia": 0.0
        }

    net_weight = sum(resolve_item_weight(it) for it in items)
    total_weight = net_weight + box_buffer_g
    is_avia = total_weight <= AVIA_MAX_WEIGHT_G
    avia_remaining = max(0, AVIA_MAX_WEIGHT_G - total_weight) if is_avia else 0
    avia_overweight = max(0, total_weight - AVIA_MAX_WEIGHT_G)
    pct = round(min(100.0, (total_weight / AVIA_MAX_WEIGHT_G) * 100.0), 1)

    return {
        "item_count": len(items),
        "net_weight_g": net_weight,
        "box_buffer_g": box_buffer_g,
        "total_weight_g": total_weight,
        "total_weight_kg": round(total_weight / 1000.0, 2),
        "is_avia_eligible": is_avia,
        "avia_remaining_g": avia_remaining,
        "avia_overweight_g": avia_overweight,
        "weight_pct_of_avia": pct
    }


def estimate_shipping_cost_by_method(
    weight_g: int,
    method_id: str,
    rate_jpy: float = DEFAULT_JPY_PLN_RATE
) -> Dict[str, Any]:
    """Calculates shipping cost in JPY and PLN for a specific shipping method and weight."""
    cfg = SHIPPING_METHODS.get(method_id)
    if not cfg:
        raise ValueError(f"Unknown shipping method: {method_id}")

    rate_jpy = float(rate_jpy or DEFAULT_JPY_PLN_RATE)
    max_weight = cfg["max_weight_g"]
    is_available = weight_g <= max_weight

    if not is_available or weight_g <= 0:
        return {
            "method_id": method_id,
            "name": cfg["name"],
            "description": cfg["description"],
            "is_available": is_available,
            "cost_jpy": 0 if weight_g <= 0 else None,
            "cost_pln": 0.0 if weight_g <= 0 else None,
            "max_weight_g": max_weight,
            "unavailability_reason": f"Przekroczono dopuszczalną wagę ({weight_g} g > {max_weight} g)" if weight_g > max_weight else None
        }

    if method_id == "avia_small_packet":
        # Base: 1,200 JPY (up to 100g) + 150 JPY per 100g
        if weight_g <= 100:
            cost_jpy = 1200
        else:
            steps = math.ceil((weight_g - 100) / 100)
            cost_jpy = 1200 + steps * 150

    elif method_id == "ems_express":
        # Base: 3,900 JPY (up to 500g)
        if weight_g <= 500:
            cost_jpy = 3900
        elif weight_g <= 2000:
            steps = math.ceil((weight_g - 500) / 250)
            cost_jpy = 3900 + steps * 350
        else:
            steps = math.ceil((weight_g - 2000) / 500)
            cost_jpy = 6000 + steps * 700

    elif method_id == "surface_sea":
        # Base: 3,300 JPY (up to 1,000g) + 450 JPY per 1,000g
        if weight_g <= 1000:
            cost_jpy = 3300
        else:
            steps = math.ceil((weight_g - 1000) / 1000)
            cost_jpy = 3300 + steps * 450
    else:
        cost_jpy = 4000

    cost_pln = round(cost_jpy * rate_jpy, 2)

    return {
        "method_id": method_id,
        "name": cfg["name"],
        "description": cfg["description"],
        "is_available": True,
        "cost_jpy": cost_jpy,
        "cost_pln": cost_pln,
        "max_weight_g": max_weight,
        "unavailability_reason": None
    }


def calculate_shipping_rates_by_weight(
    weight_g: int,
    rate_jpy: float = DEFAULT_JPY_PLN_RATE
) -> Dict[str, Any]:
    """
    Computes shipping options for all methods based on package weight.
    Recommends the best / most economical option.
    """
    rates = {}
    for mid in SHIPPING_METHODS:
        rates[mid] = estimate_shipping_cost_by_method(weight_g, mid, rate_jpy)

    # Determine recommended method
    available_methods = [r for r in rates.values() if r["is_available"] and r["cost_pln"] is not None]
    if not available_methods:
        recommended_id = "ems_express"
    elif weight_g <= AVIA_MAX_WEIGHT_G:
        recommended_id = "avia_small_packet"
    elif weight_g <= 4000:
        recommended_id = "ems_express"
    else:
        # For heavy packages > 4kg, surface sea is cheapest
        cheapest = min(available_methods, key=lambda x: x["cost_pln"])
        recommended_id = cheapest["method_id"]

    return {
        "weight_g": weight_g,
        "methods": rates,
        "recommended_method_id": recommended_id,
        "recommended": rates.get(recommended_id)
    }


def calculate_residual_profit(
    items: List[Dict[str, Any]],
    shipping_method_id: Optional[str] = None,
    rate_jpy: float = DEFAULT_JPY_PLN_RATE,
    rate_eur: float = DEFAULT_EUR_PLN_RATE
) -> Dict[str, Any]:
    """
    Calculates the exact residual net profit ('price it leaves you with' / 'cena, która zostaje')
    taking into account total package weight, selected shipping tier, ZenMarket fees, and taxes.
    """
    if not items:
        return {
            "total_items": 0,
            "total_resale_pln": 0.0,
            "total_purchase_jpy": 0,
            "total_purchase_pln": 0.0,
            "total_zenmarket_fees_pln": 0.0,
            "shipping_cost_pln": 0.0,
            "deposit_fee_pln": 0.0,
            "vat_pln": 0.0,
            "total_landed_cost_pln": 0.0,
            "residual_profit_pln": 0.0,
            "residual_roi_pct": 0.0,
            "package_weight": calculate_package_weight([])
        }

    weight_info = calculate_package_weight(items)
    shipping_info = calculate_shipping_rates_by_weight(weight_info["total_weight_g"], rate_jpy)

    chosen_method_id = shipping_method_id or shipping_info["recommended_method_id"]
    chosen_method = shipping_info["methods"].get(chosen_method_id)
    if not chosen_method or not chosen_method["is_available"]:
        chosen_method = shipping_info["recommended"]

    shipping_cost_pln = chosen_method["cost_pln"] or 0.0

    total_purchase_jpy = sum(float(it.get("price_jpy", 0)) for it in items)
    total_purchase_pln = round(total_purchase_jpy * rate_jpy, 2)

    item_count = len(items)
    domestic_zen_jpy = item_count * ZENMARKET_FEE_JPY
    domestic_zen_pln = round(domestic_zen_jpy * rate_jpy, 2)
    zen_handling_eur = item_count * ZENMARKET_FEE_EUR
    zen_handling_pln = round(zen_handling_eur * rate_eur, 2)
    total_zenmarket_fees_pln = round(domestic_zen_pln + zen_handling_pln, 2)

    total_resale_pln = round(sum(float(it.get("est_pl_value", 0)) for it in items), 2)

    subtotal_goods_and_freight = round(total_purchase_pln + total_zenmarket_fees_pln + shipping_cost_pln, 2)
    deposit_fee_pln = round(subtotal_goods_and_freight * ZENMARKET_DEPOSIT_FEE_RATE, 2)
    vat_pln = round(subtotal_goods_and_freight * VAT_RATE, 2)

    total_landed_cost_pln = round(subtotal_goods_and_freight + deposit_fee_pln + vat_pln, 2)
    residual_profit_pln = round(total_resale_pln - total_landed_cost_pln, 2)
    residual_roi_pct = round((residual_profit_pln / total_landed_cost_pln * 100.0), 1) if total_landed_cost_pln > 0 else 0.0

    return {
        "total_items": item_count,
        "total_resale_pln": total_resale_pln,
        "total_purchase_jpy": total_purchase_jpy,
        "total_purchase_pln": total_purchase_pln,
        "total_zenmarket_fees_pln": total_zenmarket_fees_pln,
        "selected_shipping_method": chosen_method["name"],
        "selected_shipping_method_id": chosen_method["method_id"],
        "shipping_cost_pln": shipping_cost_pln,
        "deposit_fee_pln": deposit_fee_pln,
        "vat_pln": vat_pln,
        "total_landed_cost_pln": total_landed_cost_pln,
        "residual_profit_pln": residual_profit_pln,
        "residual_roi_pct": residual_roi_pct,
        "package_weight": weight_info,
        "shipping_rates": shipping_info
    }


def resolve_item_battery_count(item: Dict[str, Any]) -> int:
    """
    Accurately counts lithium batteries per item.
    Detects internal batteries in handheld consoles (3DS, DS, PSP, PS Vita, GBA SP)
    and accounts for multi-device bundles (e.g. wholesale PSP lots: 3 consoles = 3 batteries).
    Returns 0 if dry-cell, no battery, or if ZenMarket dry-shipping/disposal is applied.
    """
    if not item:
        return 0

    # If already disposed or marked dry ship
    if item.get("battery_disposed") or item.get("dry_ship"):
        return 0

    # Explicit battery_count takes precedence
    if "battery_count" in item and item["battery_count"] is not None:
        try:
            return max(0, int(item["battery_count"]))
        except (ValueError, TypeError):
            pass

    b_type = str(item.get("battery_type", "")).lower()
    if b_type in ["none", "dry-cell", "0% li-ion", "dry-ship", "dry_ship"]:
        return 0

    text = " ".join([
        str(item.get("model", "")),
        str(item.get("name", "")),
        str(item.get("custom_note", "")),
        str(item.get("category_id", "")),
        str(item.get("search_query_jp", ""))
    ]).lower()

    # Multi-unit console bundle detection (e.g. wholesale PSP lots: 3台, 4台, 5台, 3 szt, 5 sztuk)
    unit_count = 1
    m = re.search(r'(\d+)\s*(?:台|szt|konsole|konsol|sztuk)', text)
    if m:
        try:
            parsed = int(m.group(1))
            if parsed > 1:
                unit_count = parsed
        except ValueError:
            pass

    # Known lithium battery devices
    li_ion_patterns = [
        "psp", "vita", "3ds", "ds lite", "dslite", "dsi", "gba sp",
        "game boy advance sp", "switch", "dualsense", "dualshock 3", "dualshock 4"
    ]

    if b_type == "li-ion":
        return unit_count
    if any(p in text for p in li_ion_patterns):
        # Exclude accessories that are just games/cases/cables/chargers without the console
        if any(acc in text for acc in ["box only", "manual only", "gra ", "game only", "silicone cover", "etui"]):
            if not any(k in text for k in ["本体", "konsola", "console"]):
                return 0
        return unit_count

    return 0


def apply_battery_disposal(
    item: Dict[str, Any],
    count_to_dispose: Optional[int] = None,
    rate_jpy: float = DEFAULT_JPY_PLN_RATE
) -> Dict[str, Any]:
    """
    Applies ZenMarket paid battery disposal service to an item.
    Fee (300 JPY per battery) is assessed.
    Item becomes 0% Li-Ion dry ship, allowing unrestricted air shipping.
    """
    item_copy = dict(item)
    current_count = resolve_item_battery_count(item)
    if count_to_dispose is None or count_to_dispose >= current_count:
        disposed = current_count
        new_battery_count = 0
        item_copy["dry_ship"] = True
        item_copy["battery_disposed"] = True
        item_copy["battery_type"] = "dry-ship"
    else:
        disposed = max(0, count_to_dispose)
        new_battery_count = max(0, current_count - disposed)
        if new_battery_count == 0:
            item_copy["dry_ship"] = True
            item_copy["battery_disposed"] = True
            item_copy["battery_type"] = "dry-ship"

    item_copy["battery_count"] = new_battery_count
    fee_jpy = disposed * ZENMARKET_BATTERY_DISPOSAL_FEE_JPY
    fee_pln = round(fee_jpy * rate_jpy, 2)
    item_copy["disposal_fee_jpy"] = fee_jpy
    item_copy["disposal_fee_pln"] = fee_pln

    return {
        "item": item_copy,
        "disposed_batteries": disposed,
        "remaining_batteries": new_battery_count,
        "disposal_fee_jpy": fee_jpy,
        "disposal_fee_pln": fee_pln,
        "is_dry_ship": item_copy.get("dry_ship", False)
    }


def calculate_marginal_freight(
    current_items: List[Dict[str, Any]],
    candidate_item: Dict[str, Any],
    shipping_method_id: Optional[str] = None,
    rate_jpy: float = DEFAULT_JPY_PLN_RATE,
    rate_eur: float = DEFAULT_EUR_PLN_RATE
) -> Dict[str, Any]:
    """
    Calculates incremental (marginal) freight cost of adding a candidate item
    to an existing parcel.
    Evaluates:
    - Weight increase and whether it pushes the parcel over the 2,000g AVIA limit into expensive EMS/DHL.
    - Marginal freight cost: new_parcel_freight - current_parcel_freight.
    - Battery capacity impact (IATA 2-device limit).
    - Whether marginal freight and associated fees erase the item's expected resale margin.
    """
    rate_jpy = float(rate_jpy or DEFAULT_JPY_PLN_RATE)
    rate_eur = float(rate_eur or DEFAULT_EUR_PLN_RATE)

    # 1. Current parcel state
    if current_items:
        curr_weight_info = calculate_package_weight(current_items)
        curr_shipping_info = calculate_shipping_rates_by_weight(curr_weight_info["total_weight_g"], rate_jpy)
        curr_method_id = shipping_method_id or curr_shipping_info["recommended_method_id"]
        curr_method = curr_shipping_info["methods"].get(curr_method_id) or curr_shipping_info["recommended"]
        curr_freight_pln = curr_method["cost_pln"] or 0.0
        curr_freight_jpy = curr_method["cost_jpy"] or 0
        curr_weight_g = curr_weight_info["total_weight_g"]
        curr_is_avia = curr_weight_info["is_avia_eligible"]
        curr_battery_audit = ConsolidationTracker.audit_battery_slots(current_items)
    else:
        curr_weight_info = calculate_package_weight([])
        curr_freight_pln = 0.0
        curr_freight_jpy = 0
        curr_method_id = "none"
        curr_method = {"name": "Brak (Pusta paczka)", "method_id": "none", "cost_pln": 0.0, "cost_jpy": 0}
        curr_weight_g = 0
        curr_is_avia = True
        curr_battery_audit = {"li_ion_count": 0, "is_compliant": True, "slots_available": MAX_LI_ION_PER_PARCEL}

    # 2. New parcel state with candidate added
    new_items = list(current_items) + [candidate_item]
    new_weight_info = calculate_package_weight(new_items)
    new_shipping_info = calculate_shipping_rates_by_weight(new_weight_info["total_weight_g"], rate_jpy)
    new_method_id = shipping_method_id or new_shipping_info["recommended_method_id"]
    new_method = new_shipping_info["methods"].get(new_method_id) or new_shipping_info["recommended"]
    new_freight_pln = new_method["cost_pln"] or 0.0
    new_freight_jpy = new_method["cost_jpy"] or 0
    new_weight_g = new_weight_info["total_weight_g"]
    new_is_avia = new_weight_info["is_avia_eligible"]
    new_battery_audit = ConsolidationTracker.audit_battery_slots(new_items)

    # 3. Incremental freight & weight
    marginal_weight_g = new_weight_g - curr_weight_g if current_items else new_weight_g
    marginal_freight_pln = round(max(0.0, new_freight_pln - curr_freight_pln), 2) if current_items else new_freight_pln
    marginal_freight_jpy = max(0, new_freight_jpy - curr_freight_jpy) if current_items else new_freight_jpy

    # 4. Weight bracket crossing check (e.g. AVIA Small Packet 2000g ceiling)
    crossed_avia_bracket = bool(current_items and curr_is_avia and not new_is_avia)
    bracket_changed = bool(current_items and (curr_method.get("method_id") != new_method.get("method_id")))

    # 5. Battery compliance check
    battery_limit_exceeded = not new_battery_audit["is_compliant"]
    cand_batteries = resolve_item_battery_count(candidate_item)

    # 6. Marginal economics & profit impact
    cand_price_jpy = float(candidate_item.get("price_jpy", candidate_item.get("target_price_jpy", 0)))
    cand_price_pln = round(cand_price_jpy * rate_jpy, 2)
    cand_zen_jpy = ZENMARKET_FEE_JPY
    cand_zen_eur = ZENMARKET_FEE_EUR
    cand_zen_pln = round(cand_zen_jpy * rate_jpy + cand_zen_eur * rate_eur, 2)
    cand_resale_pln = float(candidate_item.get("est_pl_value", 0))

    # Marginal landed cost of adding this specific item into the parcel
    marginal_subtotal = round(cand_price_pln + cand_zen_pln + marginal_freight_pln, 2)
    marginal_deposit_fee = round(marginal_subtotal * ZENMARKET_DEPOSIT_FEE_RATE, 2)
    marginal_vat = round(marginal_subtotal * VAT_RATE, 2)
    marginal_landed_cost_pln = round(marginal_subtotal + marginal_deposit_fee + marginal_vat, 2)
    marginal_net_margin_pln = round(cand_resale_pln - marginal_landed_cost_pln, 2)
    marginal_roi_pct = round((marginal_net_margin_pln / marginal_landed_cost_pln * 100.0), 1) if marginal_landed_cost_pln > 0 else 0.0

    erases_margin = bool(marginal_net_margin_pln <= 0)

    # 7. Recommendation decision
    if battery_limit_exceeded:
        recommendation = "reject_battery_limit"
        verdict = (
            f"🚫 Odrzucono: Przekroczono limit IATA baterii litowych ({new_battery_audit['li_ion_count']}/2). "
            f"Wymagany ZenMarket Dry Shipping ({new_battery_audit.get('dry_shipping_option', {}).get('disposal_fee_pln', 0):.2f} zł) lub usunięcie pozycji."
        )
    elif erases_margin:
        recommendation = "reject_marginal_freight"
        verdict = (
            f"🚫 Koszt marginalny wysyłki ({marginal_freight_pln:.2f} zł) kasuje zysk z przedmiotu! "
            f"Marża netto: {marginal_net_margin_pln:.2f} zł (brak opłacalności zakupu)."
        )
    elif crossed_avia_bracket:
        recommendation = "caution_bracket_crossed"
        verdict = (
            f"⚠️ Uwaga: Dodanie przedmiotu przekracza limit 2,000 g AVIA ({new_weight_g} g > 2000 g) "
            f"i wymusza droższy transport {new_method['name']}. Marginalny fracht: +{marginal_freight_pln:.2f} zł. "
            f"Pozostała marża netto: +{marginal_net_margin_pln:.2f} zł (ROI: {marginal_roi_pct}%)."
        )
    else:
        recommendation = "add_to_parcel"
        verdict = (
            f"✅ Opłacalne dołączenie do paczki: Marginalny fracht wynosi {marginal_freight_pln:.2f} zł. "
            f"Szacowany zysk netto z pozycji: +{marginal_net_margin_pln:.2f} zł (ROI: {marginal_roi_pct}%)."
        )

    return {
        "candidate_item": candidate_item,
        "candidate_battery_count": cand_batteries,
        "current_weight_g": curr_weight_g,
        "new_weight_g": new_weight_g,
        "marginal_weight_g": marginal_weight_g,
        "current_freight_pln": curr_freight_pln,
        "new_freight_pln": new_freight_pln,
        "marginal_freight_pln": marginal_freight_pln,
        "marginal_freight_jpy": marginal_freight_jpy,
        "current_shipping_method": curr_method.get("name"),
        "new_shipping_method": new_method.get("name"),
        "crossed_avia_bracket": crossed_avia_bracket,
        "bracket_changed": bracket_changed,
        "battery_limit_exceeded": battery_limit_exceeded,
        "candidate_price_pln": cand_price_pln,
        "candidate_zenmarket_fee_pln": cand_zen_pln,
        "candidate_resale_pln": cand_resale_pln,
        "marginal_landed_cost_pln": marginal_landed_cost_pln,
        "marginal_net_margin_pln": marginal_net_margin_pln,
        "marginal_roi_pct": marginal_roi_pct,
        "erases_margin": erases_margin,
        "recommendation": recommendation,
        "verdict": verdict,
        "battery_audit": new_battery_audit
    }


class ConsolidationTracker:
    def __init__(self, start_date=CONSOLIDATION_START, storage_limit_days=FREE_STORAGE_DAYS):
        if isinstance(start_date, str):
            self.start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        elif isinstance(start_date, datetime):
            self.start_date = start_date.date()
        elif isinstance(start_date, date):
            self.start_date = start_date
        else:
            self.start_date = date.today()

        self.storage_limit_days = int(storage_limit_days)

    def track_items_storage(
        self,
        items: List[Dict[str, Any]],
        now: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Performs per-item warehouse receipt and 60-day storage deadline tracking.
        ZenMarket 60-day free storage limit begins on each item's individual arrival date,
        not on a single global date.
        """
        if now is None:
            now_date = date.today()
        elif isinstance(now, datetime):
            now_date = now.date()
        elif isinstance(now, date):
            now_date = now
        elif isinstance(now, str):
            now_date = datetime.strptime(now, "%Y-%m-%d").date()
        else:
            now_date = date.today()

        if not items:
            timeline = self.get_timeline_status(now=now_date)
            return {
                "items_count": 0,
                "earliest_arrival_date": timeline["start_date"],
                "nearest_deadline": timeline["deadline"],
                "days_remaining_nearest": timeline["days_remaining"],
                "status_badge": timeline["status_badge"],
                "status_color": timeline["status_color"],
                "critical_items_count": 0,
                "expired_items_count": 0,
                "per_item_details": []
            }

        per_item_details = []
        for it in items:
            arr_val = (
                it.get("arrival_date")
                or it.get("warehouse_arrival_date")
                or it.get("received_at")
                or it.get("arrival")
            )
            if isinstance(arr_val, str):
                try:
                    item_arr_date = datetime.strptime(arr_val.split("T")[0], "%Y-%m-%d").date()
                except ValueError:
                    item_arr_date = self.start_date
            elif isinstance(arr_val, (datetime, date)):
                item_arr_date = arr_val.date() if isinstance(arr_val, datetime) else arr_val
            else:
                item_arr_date = self.start_date

            item_deadline = item_arr_date + timedelta(days=self.storage_limit_days)
            item_days_passed = max(0, (now_date - item_arr_date).days)
            item_days_remaining = max(0, (item_deadline - now_date).days)
            is_expired = now_date > item_deadline

            if item_days_remaining > 30:
                badge = "🟢 Bezpieczny (Okno konsolidacji)"
                color = "brightgreen"
            elif item_days_remaining > 15:
                badge = "🟡 Umiarkowany (Przygotuj listę)"
                color = "yellow"
            elif item_days_remaining > 5:
                badge = "🟠 Pilny (Twórz paczkę)"
                color = "orange"
            else:
                badge = "🔴 Krytyczny (Naliczanie opłat)"
                color = "red"

            per_item_details.append({
                "item_id": it.get("id", "unknown"),
                "model": it.get("model") or it.get("name") or "Pozycja",
                "arrival_date": item_arr_date.strftime("%Y-%m-%d"),
                "deadline": item_deadline.strftime("%Y-%m-%d"),
                "days_stored": item_days_passed,
                "days_remaining": item_days_remaining,
                "is_expired": is_expired,
                "status_badge": badge,
                "status_color": color
            })

        earliest_arr = min(d["arrival_date"] for d in per_item_details)
        nearest_deadline = min(d["deadline"] for d in per_item_details)
        days_rem_nearest = min(d["days_remaining"] for d in per_item_details)
        critical_count = sum(1 for d in per_item_details if d["days_remaining"] <= 5)
        expired_count = sum(1 for d in per_item_details if d["is_expired"])

        if days_rem_nearest > 30:
            overall_badge = f"🟢 Bezpieczny ({days_rem_nearest} dni do opłat)"
            overall_color = "brightgreen"
        elif days_rem_nearest > 15:
            overall_badge = f"🟡 Umiarkowany ({days_rem_nearest} dni do opłat)"
            overall_color = "yellow"
        elif days_rem_nearest > 5:
            overall_badge = f"🟠 Pilny ({days_rem_nearest} dni do opłat)"
            overall_color = "orange"
        else:
            overall_badge = f"🔴 Krytyczny ({days_rem_nearest} dni do naliczania opłat magazynowych!)"
            overall_color = "red"

        return {
            "items_count": len(items),
            "earliest_arrival_date": earliest_arr,
            "nearest_deadline": nearest_deadline,
            "days_remaining_nearest": days_rem_nearest,
            "status_badge": overall_badge,
            "status_color": overall_color,
            "critical_items_count": critical_count,
            "expired_items_count": expired_count,
            "per_item_details": per_item_details
        }

    def get_timeline_status(self, now=None, items=None):
        """
        Returns timeline status.
        If items are provided, evaluates per-item warehouse receipt dates.
        Otherwise falls back to tracker's global start_date.
        """
        if now is None:
            now_date = date.today()
        elif isinstance(now, datetime):
            now_date = now.date()
        elif isinstance(now, date):
            now_date = now
        elif isinstance(now, str):
            now_date = datetime.strptime(now, "%Y-%m-%d").date()
        else:
            now_date = date.today()

        if items:
            per_item = self.track_items_storage(items, now=now_date)
            days_passed = (now_date - datetime.strptime(per_item["earliest_arrival_date"], "%Y-%m-%d").date()).days
            return {
                "start_date": per_item["earliest_arrival_date"],
                "deadline": per_item["nearest_deadline"],
                "days_passed": max(0, days_passed),
                "days_remaining": per_item["days_remaining_nearest"],
                "status_badge": per_item["status_badge"],
                "status_color": per_item["status_color"],
                "free_storage_limit": self.storage_limit_days,
                "per_item_details": per_item["per_item_details"],
                "critical_items_count": per_item["critical_items_count"],
                "expired_items_count": per_item["expired_items_count"]
            }

        deadline = self.start_date + timedelta(days=self.storage_limit_days)
        days_passed = (now_date - self.start_date).days
        days_remaining = max(0, (deadline - now_date).days)

        # Determine status level
        if days_remaining > 30:
            status_badge = "🟢 Safe (Ideal consolidation window)"
            status_color = "brightgreen"
        elif days_remaining > 15:
            status_badge = "🟡 Moderate (Prepare packing list)"
            status_color = "yellow"
        elif days_remaining > 5:
            status_badge = "🟠 Urgent (Trigger package creation)"
            status_color = "orange"
        else:
            status_badge = "🔴 Critical (Storage fees imminent)"
            status_color = "red"

        return {
            "start_date": self.start_date.strftime("%Y-%m-%d"),
            "deadline": deadline.strftime("%Y-%m-%d"),
            "days_passed": max(0, days_passed),
            "days_remaining": days_remaining,
            "status_badge": status_badge,
            "status_color": status_color,
            "free_storage_limit": self.storage_limit_days
        }

    @staticmethod
    def calculate_parcel_savings(items, rate_jpy=DEFAULT_JPY_PLN_RATE):
        """
        Calculates shipping cost difference between individual packages
        vs one consolidated parcel, with full weight and shipping tier analysis.
        """
        if not items:
            return {
                "individual_cost_pln": 0,
                "consolidated_cost_pln": 0,
                "savings_pln": 0,
                "weight_g": 0,
                "weight_kg": 0.0
            }
        
        # Individual shipping estimate per small parcel JP-PL: ~110 PLN
        individual_cost = len(items) * 110
        
        # Consolidated parcel: base ~140 PLN + ~25 PLN per kg/extra item
        consolidated_cost = 140 + max(0, (len(items) - 1) * 18)
        savings = max(0, individual_cost - consolidated_cost)

        # Weight-based analysis
        weight_info = calculate_package_weight(items)
        shipping_info = calculate_shipping_rates_by_weight(weight_info["total_weight_g"], rate_jpy)
        rec_shipping_pln = shipping_info["recommended"]["cost_pln"] if shipping_info.get("recommended") else consolidated_cost

        return {
            "individual_cost_pln": individual_cost,
            "consolidated_cost_pln": consolidated_cost,
            "savings_pln": savings,
            "weight_analysis": weight_info,
            "shipping_options": shipping_info,
            "weight_based_shipping_pln": rec_shipping_pln,
            "weight_g": weight_info["total_weight_g"],
            "weight_kg": weight_info["total_weight_kg"]
        }

    @staticmethod
    def audit_battery_slots(items, rate_jpy=DEFAULT_JPY_PLN_RATE):
        """
        Audits selected items against IATA 2-battery limit for air shipping
        and Japan Post Dangerous Goods regulations for sea mail.
        Accurately counts batteries in multi-device bundles (e.g. 3 PSPs = 3 batteries).
        Provides ZenMarket paid battery disposal option (dry shipping).
        """
        rate_jpy = float(rate_jpy or DEFAULT_JPY_PLN_RATE)
        li_ion_count = sum(resolve_item_battery_count(it) for it in items) if items else 0
        slots_available = max(0, MAX_LI_ION_PER_PARCEL - li_ion_count)
        is_compliant = li_ion_count <= MAX_LI_ION_PER_PARCEL
        excess_batteries = max(0, li_ion_count - MAX_LI_ION_PER_PARCEL)

        disposal_fee_jpy = excess_batteries * ZENMARKET_BATTERY_DISPOSAL_FEE_JPY
        disposal_fee_pln = round(disposal_fee_jpy * rate_jpy, 2)

        dry_shipping_option = {
            "available": excess_batteries > 0,
            "excess_batteries": excess_batteries,
            "disposal_fee_jpy": disposal_fee_jpy,
            "disposal_fee_pln": disposal_fee_pln,
            "service_name": "ZenMarket Paid Battery Disposal (Dry Shipping)",
            "description": (
                f"Opłać utylizację {excess_batteries} baterii w ZenMarket ({disposal_fee_jpy} JPY ≈ {disposal_fee_pln:.2f} zł), "
                "aby paczka stała się w 100% compliant i mogła lecieć pocztą lotniczą bez ograniczeń."
            )
        }

        # Japan Post Dangerous Goods regulations apply to Sea Mail too!
        sea_mail_note = (
            "Zasady towarów niebezpiecznych Japan Post (Dangerous Goods) obowiązują również pocztę morską (Surface Mail). "
            "Poczta morska NIE jest darmową furtką na ominięcie limitów IATA dla baterii litowych bez deklaracji."
        )

        warning = None
        if not is_compliant:
            warning = (
                f"EXCEEDED: {li_ion_count}/{MAX_LI_ION_PER_PARCEL} Li-Ion devices! "
                f"Remove {excess_batteries} to ship via air."
            )

        return {
            "li_ion_count": li_ion_count,
            "max_allowed": MAX_LI_ION_PER_PARCEL,
            "slots_available": slots_available,
            "is_compliant": is_compliant,
            "is_air_compliant": is_compliant,
            "sea_mail_dangerous_goods_applies": True,
            "sea_mail_note": sea_mail_note,
            "excess_batteries": excess_batteries,
            "dry_shipping_option": dry_shipping_option,
            "warning": warning
        }

