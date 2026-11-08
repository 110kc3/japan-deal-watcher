"""Unit tests for HistoryTracker, HistoryGenerator, and markdown strikethrough."""

import unittest
import tempfile
import json
from pathlib import Path

from watcher.history_tracker import HistoryTracker
from watcher.history_generator import HistoryGenerator
from watcher.markdown_generator import MarkdownGenerator


class TestHistoryTracker(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.history_file = Path(self.temp_dir.name) / "price_history.json"
        self.tracker = HistoryTracker(filepath=self.history_file)

        self.sample_deals = [
            {
                "id": "item_active_01",
                "model": "Nintendo DS Lite",
                "color": "Metallic Silver",
                "category_id": "nintendo_ds_consoles",
                "category_name": "Nintendo DS & 3DS",
                "platform": "Mercari Japan",
                "price_jpy": 3500,
                "price_pln_raw": 86.91,
                "landed_cost_pln": 184.14,
                "est_pl_value": 260.00,
                "est_margin_pln": 75.86,
                "roi_percent": 41.2,
                "battery_type": "li-ion",
                "status": "Dostępne",
                "zenmarket_url": "https://zenmarket.jp/item1",
                "mercari_url": "https://jp.mercari.com/item1"
            },
            {
                "id": "item_sold_02",
                "model": "Super Takumar 55mm f/1.8",
                "color": "Black",
                "category_id": "analog_lenses",
                "category_name": "Obiektywy Analogowe",
                "platform": "Mercari Japan",
                "price_jpy": 2200,
                "price_pln_raw": 54.63,
                "landed_cost_pln": 132.50,
                "est_pl_value": 320.00,
                "est_margin_pln": 187.50,
                "roi_percent": 141.5,
                "battery_type": "none",
                "status": "Zakończone / 404",
                "zenmarket_url": "https://zenmarket.jp/item2",
                "mercari_url": "https://jp.mercari.com/item2"
            }
        ]

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_record_scan_initializes_items_and_sales(self):
        res = self.tracker.record_scan(self.sample_deals)
        self.assertEqual(res["total_tracked"], 2)
        self.assertEqual(res["total_sales"], 1)
        self.assertEqual(res["new_sales"], 1)

        # File persisted
        self.assertTrue(self.history_file.exists())
        with open(self.history_file, "r", encoding="utf-8") as f:
            saved = json.load(f)
        self.assertIn("item_active_01", saved["items"])
        self.assertIn("item_sold_02", saved["items"])
        self.assertEqual(len(saved["sales_log"]), 1)
        self.assertEqual(saved["sales_log"][0]["id"], "item_sold_02")

    def test_price_change_detection(self):
        # 1. Initial scan
        self.tracker.record_scan(self.sample_deals)

        # 2. Price cut on item_active_01
        updated_deals = [
            dict(self.sample_deals[0], price_jpy=3000, price_pln_raw=74.50),
            self.sample_deals[1]
        ]
        res = self.tracker.record_scan(updated_deals)
        self.assertEqual(res["price_changes"], 1)

        item = self.tracker.data["items"]["item_active_01"]
        self.assertEqual(len(item["price_history"]), 2)
        self.assertEqual(item["current_price_jpy"], 3000)

    def test_active_to_sold_transition(self):
        # 1. Initial scan with item_active_01 as active
        self.tracker.record_scan([self.sample_deals[0]])
        self.assertEqual(len(self.tracker.data["sales_log"]), 0)

        # 2. Second scan: item is sold (404)
        sold_item = dict(self.sample_deals[0], status="Zakończone / 404")
        res = self.tracker.record_scan([sold_item])
        self.assertEqual(res["new_sales"], 1)
        self.assertEqual(len(self.tracker.data["sales_log"]), 1)
        self.assertEqual(self.tracker.data["sales_log"][0]["id"], "item_active_01")
        self.assertTrue(self.tracker.data["items"]["item_active_01"]["is_sold"])

    def test_analytics_computation(self):
        self.tracker.record_scan(self.sample_deals)
        analytics = self.tracker.get_analytics()

        self.assertEqual(analytics["total_tracked"], 2)
        self.assertEqual(analytics["total_active"], 1)
        self.assertEqual(analytics["total_sales"], 1)
        self.assertEqual(analytics["avg_price_jpy"], 2200.0)
        self.assertEqual(analytics["avg_margin_pln"], 187.50)
        self.assertEqual(len(analytics["category_stats"]), 1)
        self.assertGreater(len(analytics["sweet_spots"]), 0)

    def test_history_generator_renders_markdown(self):
        self.tracker.record_scan(self.sample_deals)
        gen = HistoryGenerator(self.tracker)
        md = gen.generate()

        self.assertIn("# 📈 Historia Cen, Transakcji i Analiza Sprzedaży", md)
        self.assertIn("Kluczowe Wskaźniki Zrealizowanej Sprzedaży", md)
        self.assertIn("Co Się Najszybciej Sprzedaje?", md)
        self.assertIn("Złote Widełki Cenowe", md)
        self.assertIn("Kompletny Rejestr Zamkniętych i Sprzedanych Ofert", md)
        self.assertIn("Super Takumar 55mm f/1.8", md)
        self.assertIn("```mermaid", md)

    def test_markdown_generator_strikethrough_for_ended_deals(self):
        timeline = {
            "start_date": "2026-11-07",
            "deadline": "2027-01-06",
            "days_remaining": 59,
            "days_passed": 1,
            "status_badge": "🟢 Bezpiecznie"
        }
        md_gen = MarkdownGenerator(
            deals=self.sample_deals,
            timeline_status=timeline,
            rate=0.024832,
            rate_eur=4.35
        )
        md = md_gen.generate()

        # Active deal is NOT strikethrough
        self.assertIn("**Nintendo DS Lite**", md)
        self.assertNotIn("~~**Nintendo DS Lite**~~", md)

        # Ended / sold deal IS strikethrough (user rule: "kiedy oferta sie skonczy wykresl ja z readme")
        self.assertIn("~~**Super Takumar 55mm f/1.8**~~", md)
        self.assertIn("~~❌ Zakończone / Sprzedane~~", md)


if __name__ == "__main__":
    unittest.main()
