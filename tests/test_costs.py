import unittest
from watcher.costs import calculate_landed_cost
from watcher.config import (
    DEFAULT_JPY_PLN_RATE,
    DEFAULT_EUR_PLN_RATE,
    ZENMARKET_FEE_JPY,
    ZENMARKET_FEE_EUR,
    ZENMARKET_DEPOSIT_FEE_RATE,
    VAT_RATE
)

class TestCosts(unittest.TestCase):
    def test_calculate_landed_cost_structure(self):
        # 10,000 JPY, ps_vita category (shipping = 35 PLN)
        rate_jpy = 0.024832
        rate_eur = 4.35
        res = calculate_landed_cost(10000, "ps_vita", rate_jpy=rate_jpy, rate_eur=rate_eur)

        self.assertEqual(res["price_jpy"], 10000)
        self.assertEqual(res["price_pln_raw"], 248.32)
        self.assertEqual(res["domestic_shipping_jpy"], 800)
        self.assertEqual(res["domestic_shipping_pln"], 19.87)
        self.assertEqual(res["zenmarket_fee_eur"], 2.0)
        self.assertEqual(res["zenmarket_fee_pln"], 8.70)
        self.assertEqual(res["shipping_share_pln"], 35.0)

        # base_purchase = 248.32 + 19.87 + 8.70 = 276.89 PLN
        # subtotal = 276.89 + 35.0 = 311.89 PLN
        # deposit = 311.89 * 0.035 = 10.92 PLN
        # vat = 311.89 * 0.23 = 71.73 PLN
        # landed_cost = 276.89 + 35.0 + 10.92 + 71.73 = 394.54 PLN
        self.assertEqual(res["deposit_fee_pln"], 10.92)
        self.assertEqual(res["vat_pln"], 71.73)
        self.assertEqual(res["landed_cost_pln"], 394.54)

    def test_calculate_landed_cost_zero_price(self):
        res = calculate_landed_cost(0, "psp_games_mix", rate_jpy=0.025, rate_eur=4.0)
        # domestic: 800 * 0.025 = 20.0 PLN
        # zenmarket: 2.0 * 4.0 = 8.0 PLN
        # base_purchase = 28.0 PLN
        # shipping_share = 20.0 PLN
        # subtotal = 48.0 PLN
        # deposit = 48.0 * 0.035 = 1.68 PLN
        # vat = 48.0 * 0.23 = 11.04 PLN
        # landed_cost = 28.0 + 20.0 + 1.68 + 11.04 = 60.72 PLN
        self.assertEqual(res["landed_cost_pln"], 60.72)

    def test_calculate_max_sniper_bid(self):
        from watcher.costs import calculate_max_sniper_bid
        rate_jpy = 0.024832
        rate_eur = 4.35
        # 890 PLN market value, ps_vita, 30% target ROI
        res = calculate_max_sniper_bid(890.0, "ps_vita", target_roi_pct=30.0, rate_jpy=rate_jpy, rate_eur=rate_eur)
        self.assertGreater(res["max_bid_jpy"], 10000)
        self.assertLessEqual(res["landed_cost_at_cap"], 890.0 / 1.30 + 1.0) # tolerance due to 100 JPY rounding
        self.assertGreaterEqual(res["guaranteed_roi_pct"], 30.0)
        self.assertGreater(res["guaranteed_margin_pln"], 200.0)

if __name__ == "__main__":
    unittest.main()
