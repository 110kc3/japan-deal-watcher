"""Cost calculation module for Japanese imports via ZenMarket.

Includes:
- Japanese item listing price in JPY (converted via live NBP rate)
- 800 JPY per item domestic shipping / local handling in Japan
- 2.0 EUR per item ZenMarket service & processing fee (converted via live NBP EUR rate)
- Category-aware consolidated international shipping share
- 3.5% payment gateway / deposit fee for top-up funds in ZenMarket
- 23% Polish VAT on customs value (goods + international shipping)
"""

from .config import (
    DEFAULT_JPY_PLN_RATE,
    DEFAULT_EUR_PLN_RATE,
    ZENMARKET_FEE_JPY,
    ZENMARKET_FEE_EUR,
    ZENMARKET_DEPOSIT_FEE_RATE,
    VAT_RATE,
    CATEGORY_SHIPPING_SHARES,
    DEFAULT_SHIPPING_SHARE_PLN,
)

def calculate_landed_cost(
    price_jpy: float,
    category_id: str = None,
    rate_jpy: float = DEFAULT_JPY_PLN_RATE,
    rate_eur: float = DEFAULT_EUR_PLN_RATE,
    shipping_share_pln: float = None
) -> dict:
    """Calculates comprehensive landed cost in Poland with full fee itemization."""
    price_jpy = max(0.0, float(price_jpy or 0))
    rate_jpy = float(rate_jpy or DEFAULT_JPY_PLN_RATE)
    rate_eur = float(rate_eur or DEFAULT_EUR_PLN_RATE)

    if shipping_share_pln is None:
        shipping_share = CATEGORY_SHIPPING_SHARES.get(category_id, DEFAULT_SHIPPING_SHARE_PLN)
    else:
        shipping_share = float(shipping_share_pln)

    price_pln_raw = round(price_jpy * rate_jpy, 2)
    domestic_shipping_pln = round(ZENMARKET_FEE_JPY * rate_jpy, 2)
    zenmarket_fee_pln = round(ZENMARKET_FEE_EUR * rate_eur, 2)

    base_purchase_pln = round(price_pln_raw + domestic_shipping_pln + zenmarket_fee_pln, 2)
    subtotal_goods_and_freight = round(base_purchase_pln + shipping_share, 2)

    deposit_fee_pln = round(subtotal_goods_and_freight * ZENMARKET_DEPOSIT_FEE_RATE, 2)

    vat_pln = round(subtotal_goods_and_freight * VAT_RATE, 2)

    landed_cost_pln = round(base_purchase_pln + shipping_share + deposit_fee_pln + vat_pln, 2)

    return {
        "price_jpy": price_jpy,
        "price_pln_raw": price_pln_raw,
        "domestic_shipping_jpy": ZENMARKET_FEE_JPY,
        "domestic_shipping_pln": domestic_shipping_pln,
        "zenmarket_fee_eur": ZENMARKET_FEE_EUR,
        "zenmarket_fee_pln": zenmarket_fee_pln,
        "shipping_share_pln": shipping_share,
        "deposit_fee_pln": deposit_fee_pln,
        "vat_pln": vat_pln,
        "landed_cost_pln": landed_cost_pln,
    }

def calculate_max_sniper_bid(
    est_pl_value: float,
    category_id: str = None,
    target_roi_pct: float = 30.0,
    rate_jpy: float = DEFAULT_JPY_PLN_RATE,
    rate_eur: float = DEFAULT_EUR_PLN_RATE,
    shipping_share_pln: float = None
) -> dict:
    """Calculates the maximum bid in JPY (Hard Sniping Cap) to guarantee target minimum ROI."""
    est_pl_value = max(0.0, float(est_pl_value or 0))
    target_roi_pct = max(5.0, float(target_roi_pct or 30.0))
    rate_jpy = float(rate_jpy or DEFAULT_JPY_PLN_RATE)
    rate_eur = float(rate_eur or DEFAULT_EUR_PLN_RATE)

    if shipping_share_pln is None:
        shipping_share = CATEGORY_SHIPPING_SHARES.get(category_id, DEFAULT_SHIPPING_SHARE_PLN)
    else:
        shipping_share = float(shipping_share_pln)

    tax_multiplier = 1.0 + ZENMARKET_DEPOSIT_FEE_RATE + VAT_RATE

    target_max_landed = est_pl_value / (1.0 + target_roi_pct / 100.0)

    subtotal_target = target_max_landed / tax_multiplier

    domestic_shipping_pln = ZENMARKET_FEE_JPY * rate_jpy
    zenmarket_fee_pln = ZENMARKET_FEE_EUR * rate_eur
    fixed_fees_pln = domestic_shipping_pln + zenmarket_fee_pln + shipping_share

    max_price_pln = max(0.0, subtotal_target - fixed_fees_pln)

    max_price_jpy = int(max_price_pln / rate_jpy // 100 * 100) if rate_jpy > 0 else 0

    verif = calculate_landed_cost(
        price_jpy=max_price_jpy,
        category_id=category_id,
        rate_jpy=rate_jpy,
        rate_eur=rate_eur,
        shipping_share_pln=shipping_share
    )
    actual_landed = verif["landed_cost_pln"]
    actual_margin = round(est_pl_value - actual_landed, 2)
    actual_roi = round(actual_margin / actual_landed * 100.0, 1) if actual_landed > 0 else 0.0

    return {
        "max_bid_jpy": max_price_jpy,
        "target_roi_pct": target_roi_pct,
        "est_pl_value": est_pl_value,
        "landed_cost_at_cap": actual_landed,
        "guaranteed_margin_pln": actual_margin,
        "guaranteed_roi_pct": actual_roi
    }
