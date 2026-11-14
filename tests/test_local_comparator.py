"""Unit tests for Local vs Import Sourcing Comparator (Task 9)."""

import unittest
from watcher.local_comparator import LocalComparator, compare_sourcing
from watcher.config import DEFAULT_JPY_PLN_RATE, DEFAULT_EUR_PLN_RATE

class TestLocalComparator(unittest.TestCase):
    def setUp(self):
        self.comparator = LocalComparator(
            rate_jpy=DEFAULT_JPY_PLN_RATE,
            rate_eur=DEFAULT_EUR_PLN_RATE
        )

    def test_recommend_skip_import_when_local_is_strictly_cheaper(self):
        """When item is cheaper to buy in Poland than importing from Japan, recommend Skip Import."""
        jp_deal = {
            "model": "Sony PSP-3000 Piano Black",
            "category_id": "psp_handheld",
            "price_jpy": 6000,
            "shipping_share_pln": 30.0
        }
        local_deal = {
            "platform": "OLX",
            "price_pln": 170.0,
            "shipping_pln": 15.0,
            "transit_days": 2
        }

        res = self.comparator.compare(jp_deal, local_deal)
        self.assertEqual(res["recommendation"], "skip_import")
        self.assertIn("Skip Import: Kup lokalnie w Polsce", res["recommendation_label"])
        self.assertGreater(res["cost_difference_pln"], 0)
        self.assertEqual(res["days_saved"], 19)
        self.assertTrue(res["local_sourcing"]["return_rights"])
        self.assertFalse(res["jp_sourcing"]["return_rights"])
        self.assertIn("niższa niż efektywny koszt", res["reason"])

    def test_recommend_skip_import_when_comparable_cost(self):
        """When local price is only slightly higher (within tolerance), transit time and return rights tip the scale."""
        jp_deal = {
            "model": "Nintendo DS Lite White",
            "category_id": "nintendo_ds_handhelds",
            "price_jpy": 3000,
            "shipping_share_pln": 30.0
        }
        local_deal = {
            "platform": "Allegro",
            "price_pln": 185.0,
            "has_smart": True,
            "transit_days": 1
        }

        res = self.comparator.compare(jp_deal, local_deal, tolerance_pln=15.0)
        self.assertEqual(res["recommendation"], "skip_import")
        self.assertIn("Skip Import: Kup lokalnie w Polsce", res["recommendation_label"])
        self.assertIn("Różnica kosztów jest znikoma", res["reason"])
        self.assertIn("UOKiK", res["reason"])

    def test_recommend_import_japan_when_arbitrage_margin_is_high(self):
        """When Japanese item is significantly cheaper than domestic market, recommend Import from Japan."""
        jp_deal = {
            "model": "New Nintendo 3DS LL Metallic Blue",
            "category_id": "nintendo_3ds_handhelds",
            "price_jpy": 9000,
            "shipping_share_pln": 30.0
        }
        local_deal = {
            "platform": "Allegro",
            "price_pln": 650.0,
            "shipping_pln": 0.0,
            "transit_days": 2
        }

        res = self.comparator.compare(jp_deal, local_deal)
        self.assertEqual(res["recommendation"], "import_japan")
        self.assertIn("Importuj z Japonii", res["recommendation_label"])
        self.assertLess(res["cost_difference_pln"], -150.0)
        self.assertIn("pozostaje wysoce opłacalny", res["reason"])

    def test_convenience_helper_function(self):
        """Tests standalone compare_sourcing convenience function."""
        jp_deal = {"price_jpy": 10000, "category_id": "ps_vita"}
        local_deal = {"price_pln": 500.0, "shipping_pln": 15.0}

        res = compare_sourcing(jp_deal, local_deal)
        self.assertIn("recommendation", res)
        self.assertIn(res["recommendation"], ["skip_import", "import_japan"])

    def test_evaluate_multiple_local_candidates(self):
        """Tests picking best local option among multiple Polish listings."""
        jp_deal = {
            "model": "GBA SP AGS-001",
            "category_id": "gameboy_advance_retro",
            "price_jpy": 4000
        }
        candidates = [
            {"platform": "Allegro (Drogi)", "price_pln": 350.0, "shipping_pln": 15.0},
            {"platform": "OLX (Średni)", "price_pln": 220.0, "shipping_pln": 15.0},
            {"platform": "Allegro Lokalnie (Tani)", "price_pln": 160.0, "has_smart": True}
        ]
        best = self.comparator.evaluate_candidates(jp_deal, candidates)
        self.assertEqual(best["local_sourcing"]["platform"], "Allegro Lokalnie (Tani)")
        self.assertEqual(best["local_sourcing"]["effective_cost_pln"], 160.0)
        self.assertEqual(best["recommendation"], "skip_import")

    def test_evaluate_candidates_empty_list(self):
        """When no local listings exist, default to importing from Japan."""
        jp_deal = {
            "model": "WonderSwan Color Final Fantasy Limited",
            "category_id": "nintendo_retro",
            "price_jpy": 5000
        }
        res = self.comparator.evaluate_candidates(jp_deal, [])
        self.assertEqual(res["recommendation"], "import_japan")
        self.assertIn("Brak ofert", res["recommendation_label"])
        self.assertIsNone(res["local_sourcing"])

if __name__ == "__main__":
    unittest.main()
