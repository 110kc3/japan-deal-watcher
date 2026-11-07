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
        self.assertGreaterEqual(ranked[1]["score"], ranked[2]["score"])

    def test_optimal_consolidation_basket(self):
        basket = self.analyzer.get_optimal_consolidation_basket()
        # Basket must respect max 2 Li-Ion items
        self.assertLessEqual(basket["li_ion_count"], 2)
        self.assertGreater(basket["total_margin_pln"], 0)
        self.assertGreater(basket["total_items"], 0)

if __name__ == "__main__":
    unittest.main()
