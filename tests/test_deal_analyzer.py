import unittest
from watcher.deal_analyzer import DealAnalyzer

class TestDealAnalyzer(unittest.TestCase):
    def setUp(self):
        self.sample_deals = [
            {
                "id": "m_high_profit",
                "model": "PSP UMD 20 sztuk",
                "color": "Mix 20 Gier",
                "category_id": "psp_games_mix",
                "category_name": "Pakiety Gier Retro PSP",
                "price_jpy": 2780,
                "price_pln_raw": 69.0,
                "landed_cost_pln": 105.0,
                "est_pl_value": 500.0,
                "est_margin_pln": 395.0,
                "roi_percent": 376.2,
                "battery_type": "none",
                "status": "Dostępne"
            },
            {
                "id": "m_vita_deal",
                "model": "PCH-2000 ZA23",
                "color": "Aqua Blue",
                "category_id": "ps_vita",
                "category_name": "PlayStation Vita",
                "price_jpy": 16000,
                "price_pln_raw": 397.0,
                "landed_cost_pln": 546.0,
                "est_pl_value": 880.0,
                "est_margin_pln": 334.0,
                "roi_percent": 61.2,
                "battery_type": "li-ion",
                "status": "Dostępne"
            },
            {
                "id": "m_low_margin",
                "model": "Old Cable",
                "color": "Black",
                "category_id": "retro_consoles_no_battery",
                "category_name": "Konsole Retro",
                "price_jpy": 8000,
                "price_pln_raw": 198.0,
                "landed_cost_pln": 300.0,
                "est_pl_value": 320.0,
                "est_margin_pln": 20.0,
                "roi_percent": 6.7,
                "battery_type": "dry-cell",
                "status": "Dostępne"
            },
            {
                "id": "m_sold_item",
                "model": "Sold Vita",
                "color": "White",
                "category_id": "ps_vita",
                "price_jpy": 15000,
                "status": "Zakończone / Sprzedane"
            }
        ]
        self.analyzer = DealAnalyzer(self.sample_deals)

    def test_high_profit_deal_analysis(self):
        result = self.analyzer.analyze_deal(self.sample_deals[0])
        self.assertEqual(result["tier"], "S-TIER")
        self.assertTrue(result["is_worth_buying"])
        self.assertGreaterEqual(result["score"], 80)
        self.assertIn("KUPUJ NATYCHMIAST", result["verdict"])
        self.assertTrue(result["is_no_battery"])

    def test_sold_item_filtering(self):
        result = self.analyzer.analyze_deal(self.sample_deals[3])
        self.assertFalse(result["is_active"])
        self.assertFalse(result["is_worth_buying"])
        self.assertEqual(result["tier"], "INACTIVE")

    def test_ranking_order(self):
        ranked = self.analyzer.get_ranked_deals()
        self.assertEqual(len(ranked), 3)  # Sold item omitted
        self.assertGreaterEqual(ranked[0]["score"], ranked[1]["score"])

    def test_broken_item_exclusion(self):
        broken_deal = {
            "id": "m_broken_cube",
            "model": "Broken GameCube",
            "is_broken": True,
            "condition_type": "broken",
            "status": "Wykluczone: Uszkodzone (Broken)"
        }
        res = self.analyzer.analyze_deal(broken_deal)
        self.assertFalse(res["is_active"])
        self.assertFalse(res["is_worth_buying"])
        self.assertEqual(res["tier"], "EXCLUDED")
        self.assertIn("WYKLUCZONE", res["verdict"])

    def test_untested_opportunity_scoring(self):
        untested_deal = {
            "id": "m_untested_psp_go",
            "model": "PSP Go Untested",
            "color": "Piano Black",
            "category_id": "psp_go",
            "price_jpy": 20000,
            "price_pln_raw": 496.0,
            "landed_cost_pln": 660.0,
            "est_pl_value": 1000.0,
            "est_margin_pln": 340.0,
            "roi_percent": 51.5,
            "battery_type": "li-ion",
            "status": "Dostępne",
            "condition_type": "untested_opportunity",
            "condition_badge": "⚡ Niesprawdzany (Potencjał Zysku)"
        }
        res = self.analyzer.analyze_deal(untested_deal)
        self.assertTrue(res["is_active"])
        self.assertTrue(res["is_worth_buying"])
        self.assertIn("⚡", res["rationale"])
        self.assertIn("arbitraż", res["rationale"])

    def test_optimal_consolidation_basket(self):
        basket = self.analyzer.get_optimal_consolidation_basket()
        # Basket must respect max 2 Li-Ion items
        self.assertLessEqual(basket["li_ion_count"], 2)
        self.assertGreater(basket["total_margin_pln"], 0)
        self.assertGreater(basket["total_items"], 0)

    def test_ps5_limited_controller_deal(self):
        ps5_deal = {
            "id": "m_ps5_gow",
            "model": "DualSense God of War Ragnarök Limited Edition",
            "color": "Two-Tone Blue",
            "category_id": "ps5_limited_controllers",
            "price_jpy": 7990,
            "price_pln_raw": 198.0,
            "landed_cost_pln": 283.0,
            "est_pl_value": 550.0,
            "est_margin_pln": 267.0,
            "roi_percent": 94.3,
            "battery_type": "li-ion",
            "status": "Dostępne",
            "condition_type": "confirmed_working"
        }
        res = self.analyzer.analyze_deal(ps5_deal)
        self.assertTrue(res["is_active"])
        self.assertTrue(res["is_worth_buying"])
        self.assertEqual(res["tier"], "S-TIER")
        self.assertFalse(res["is_no_battery"])

    def test_retro_controller_deal_no_battery(self):
        retro_deal = {
            "id": "m_ps2_slime",
            "model": "HORI Dragon Quest Slime Controller PS2",
            "color": "Slime Blue",
            "category_id": "ps_retro_limited_controllers",
            "price_jpy": 4800,
            "price_pln_raw": 119.0,
            "landed_cost_pln": 192.0,
            "est_pl_value": 450.0,
            "est_margin_pln": 258.0,
            "roi_percent": 134.4,
            "battery_type": "none",
            "status": "Dostępne",
            "condition_type": "confirmed_working"
        }
        res = self.analyzer.analyze_deal(retro_deal)
        self.assertTrue(res["is_active"])
        self.assertTrue(res["is_worth_buying"])
        self.assertEqual(res["tier"], "S-TIER")
        self.assertTrue(res["is_no_battery"])

    def test_ps_limited_console_deal(self):
        console_deal = {
            "id": "m_psone_combo",
            "model": "PSone COMBO SCPH-130",
            "color": "White Combo",
            "category_id": "ps_limited_consoles",
            "price_jpy": 25800,
            "price_pln_raw": 640.0,
            "landed_cost_pln": 863.0,
            "est_pl_value": 1600.0,
            "est_margin_pln": 737.0,
            "roi_percent": 85.4,
            "battery_type": "none",
            "status": "Dostępne",
            "condition_type": "confirmed_working"
        }
        res = self.analyzer.analyze_deal(console_deal)
        self.assertTrue(res["is_active"])
        self.assertTrue(res["is_worth_buying"])
        self.assertEqual(res["tier"], "S-TIER")
        self.assertTrue(res["is_no_battery"])

    def test_film_cameras_point_shoot_deal(self):
        camera_deal = {
            "id": "m_nikon_pikaichi",
            "model": "Nikon L35AF ISO 400 Pikaichi",
            "color": "Black",
            "category_id": "film_cameras_point_shoot",
            "price_jpy": 7980,
            "price_pln_raw": 198.0,
            "landed_cost_pln": 284.0,
            "est_pl_value": 750.0,
            "est_margin_pln": 466.0,
            "roi_percent": 164.1,
            "battery_type": "none",
            "status": "Dostępne",
            "condition_type": "confirmed_working"
        }
        res = self.analyzer.analyze_deal(camera_deal)
        self.assertTrue(res["is_active"])
        self.assertTrue(res["is_worth_buying"])
        self.assertEqual(res["tier"], "S-TIER")
        self.assertTrue(res["is_no_battery"])

if __name__ == "__main__":
    unittest.main()
