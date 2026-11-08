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

    # 3.5% deposit processing fee on all funds deposited into ZenMarket balance
    deposit_fee_pln = round(subtotal_goods_and_freight * ZENMARKET_DEPOSIT_FEE_RATE, 2)

    # 23% VAT assessed on customs value (goods + international shipping)
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
