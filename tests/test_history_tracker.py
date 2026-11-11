"""Unit tests for HistoryTracker, HistoryGenerator, and markdown strikethrough.

Fix F07 verification:
- 404s, connection errors, and exclusion filters must NOT be marked as sales.
- Genuine sales (e.g. 'Zakończone / Sprzedane') are properly logged.
- Contaminated historical entries are cleaned.
"""

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
                "status": "Zakończone / Sprzedane",
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
        self.assertTrue(saved["items"]["item_sold_02"]["is_sold"])
        self.assertFalse(saved["items"]["item_active_01"]["is_sold"])

    def test_errors_and_404_not_marked_as_sold(self):
        """Fix F07: 404s, connection errors, exclusions, and trading must NOT be marked as sales."""
        non_sales_deals = [
            {
                "id": "item_404",
                "model": "Removed Item",
                "price_jpy": 4000,
                "status": "Zakończone / 404"
            },
            {
                "id": "item_err",
                "model": "Timeout Item",
                "price_jpy": 5000,
                "status": "Błąd połączenia"
            },
            {
                "id": "item_broken",
                "model": "Broken Screen GBA",
                "price_jpy": 3000,
                "is_broken": True,
                "status": "Wykluczone: Uszkodzone (Broken)"
            },
            {
                "id": "item_trading",
                "model": "In Checkout Cart",
                "price_jpy": 6000,
                "status": "W trakcie transakcji"
            }
        ]

        res = self.tracker.record_scan(non_sales_deals)
        self.assertEqual(res["new_sales"], 0)
        self.assertEqual(res["total_sales"], 0)
        self.assertEqual(len(self.tracker.data["sales_log"]), 0)

        items = self.tracker.data["items"]
        # 404 is marked disappeared, not sold
        self.assertFalse(items["item_404"]["is_sold"])
        self.assertTrue(items["item_404"]["is_disappeared"])
        self.assertIsNone(items["item_404"]["sold_at"])

        # Connection error is marked as error, not sold
        self.assertFalse(items["item_err"]["is_sold"])
        self.assertTrue(items["item_err"]["has_fetch_error"])
        self.assertIsNone(items["item_err"]["sold_at"])

        # Broken exclusion is marked excluded, not sold
        self.assertFalse(items["item_broken"]["is_sold"])
        self.assertTrue(items["item_broken"]["is_excluded"])
        self.assertIsNone(items["item_broken"]["sold_at"])

        # In-transaction is marked trading, not sold
        self.assertFalse(items["item_trading"]["is_sold"])
        self.assertTrue(items["item_trading"]["is_trading"])
        self.assertIsNone(items["item_trading"]["sold_at"])

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

        # 2. Transition to 404: must NOT record sale
        disappeared_item = dict(self.sample_deals[0], status="Zakończone / 404")
        res_404 = self.tracker.record_scan([disappeared_item])
        self.assertEqual(res_404["new_sales"], 0)
        self.assertFalse(self.tracker.data["items"]["item_active_01"]["is_sold"])
        self.assertTrue(self.tracker.data["items"]["item_active_01"]["is_disappeared"])

        # 3. Transition to genuine sale: records sale
        sold_item = dict(self.sample_deals[0], status="Zakończone / Sprzedane")
        res_sold = self.tracker.record_scan([sold_item])
        self.assertEqual(res_sold["new_sales"], 1)
        self.assertEqual(len(self.tracker.data["sales_log"]), 1)
        self.assertEqual(self.tracker.data["sales_log"][0]["id"], "item_active_01")
        self.assertTrue(self.tracker.data["items"]["item_active_01"]["is_sold"])

    def test_clean_contaminated_entries(self):
        """Fix F07: verifies purging of 404s and errors from legacy price_history database."""
        contaminated = {
            "metadata": {"total_sales_recorded": 4, "total_tracked_items": 4},
            "items": {
                "it_404": {"status": "Zakończone / 404", "is_sold": True, "sold_at": "2026-11-08 12:00 UTC"},
                "it_broken": {"status": "Wykluczone: Uszkodzone (Broken)", "is_sold": True, "sold_at": "2026-11-08 12:00 UTC"},
                "it_err": {"status": "Błąd połączenia", "is_sold": True, "sold_at": "2026-11-08 12:00 UTC"},
                "it_real": {"status": "Zakończone / Sprzedane", "is_sold": True, "sold_at": "2026-11-08 12:00 UTC"}
            },
            "sales_log": [
                {"id": "it_404", "status": "Zakończone / 404", "realized_margin_pln": 100},
                {"id": "it_broken", "status": "Wykluczone: Uszkodzone (Broken)", "realized_margin_pln": 50},
                {"id": "it_err", "status": "Błąd połączenia", "realized_margin_pln": 80},
                {"id": "it_real", "status": "Zakończone / Sprzedane", "realized_margin_pln": 200}
            ]
        }
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(contaminated, f)

        # Reload tracker which triggers clean_contaminated_entries
        tracker = HistoryTracker(filepath=self.history_file)
        self.assertEqual(len(tracker.data["sales_log"]), 1)
        self.assertEqual(tracker.data["sales_log"][0]["id"], "it_real")
        self.assertEqual(tracker.data["metadata"]["total_sales_recorded"], 1)

        # Check item cleaning
        self.assertFalse(tracker.data["items"]["it_404"]["is_sold"])
        self.assertTrue(tracker.data["items"]["it_404"]["is_disappeared"])
        self.assertFalse(tracker.data["items"]["it_broken"]["is_sold"])
        self.assertTrue(tracker.data["items"]["it_broken"]["is_excluded"])
        self.assertFalse(tracker.data["items"]["it_err"]["is_sold"])
        self.assertTrue(tracker.data["items"]["it_err"]["has_fetch_error"])
        self.assertTrue(tracker.data["items"]["it_real"]["is_sold"])

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
