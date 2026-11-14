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

        self.assertEqual(res["deposit_fee_pln"], 10.92)
        self.assertEqual(res["vat_pln"], 71.73)
        self.assertEqual(res["landed_cost_pln"], 394.54)

    def test_calculate_landed_cost_zero_price(self):
        res = calculate_landed_cost(0, "psp_games_mix", rate_jpy=0.025, rate_eur=4.0)
        self.assertEqual(res["landed_cost_pln"], 60.72)

    def test_calculate_max_sniper_bid(self):
        from watcher.costs import calculate_max_sniper_bid
        rate_jpy = 0.024832
        rate_eur = 4.35
        res = calculate_max_sniper_bid(890.0, "ps_vita", target_roi_pct=30.0, rate_jpy=rate_jpy, rate_eur=rate_eur)
        self.assertGreater(res["max_bid_jpy"], 10000)
        self.assertLessEqual(res["landed_cost_at_cap"], 890.0 / 1.30 + 1.0)
        self.assertGreaterEqual(res["guaranteed_roi_pct"], 30.0)
        self.assertGreater(res["guaranteed_margin_pln"], 200.0)

if __name__ == "__main__":
    unittest.main()
