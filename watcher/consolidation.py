"""Consolidation, weight analysis, and 60-day packing timeline tracker."""

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

    def get_timeline_status(self, now=None):
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
    def audit_battery_slots(items):
        """
        Audits selected items against IATA 2-battery limit.
        """
        li_ion_count = sum(1 for it in items if it.get("battery_type") == "li-ion")
        slots_available = max(0, MAX_LI_ION_PER_PARCEL - li_ion_count)
        is_compliant = li_ion_count <= MAX_LI_ION_PER_PARCEL
        
        return {
            "li_ion_count": li_ion_count,
            "max_allowed": MAX_LI_ION_PER_PARCEL,
            "slots_available": slots_available,
            "is_compliant": is_compliant,
            "warning": None if is_compliant else f"EXCEEDED: {li_ion_count}/{MAX_LI_ION_PER_PARCEL} Li-Ion devices! Remove {li_ion_count - MAX_LI_ION_PER_PARCEL} to ship via air."
        }

