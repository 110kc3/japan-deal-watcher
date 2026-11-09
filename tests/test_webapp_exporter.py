import json
import tempfile
import unittest
from pathlib import Path

from watcher.webapp_exporter import WebappExporter
from watcher.config import DEFAULT_JPY_PLN_RATE, DEFAULT_EUR_PLN_RATE, MAX_CAMERA_PRICE_PLN, MAX_LENS_PRICE_PLN


class TestWebappExporter(unittest.TestCase):
    def setUp(self):
        self.sample_yahoo = [
            {
                "id": "new_n3ds_xl_red",
                "model": "New Nintendo 3DS LL (New 3DS XL)",
                "color": "Metallic Blue (RED-001)",
                "platform": "Yahoo! Auctions Japan",
                "category_id": "nintendo_3ds_handhelds",
                "category_name": "Nintendo 3DS & New 3DS",
                "battery_type": "li-ion",
                "price_jpy": 12500,
                "est_pl_value": 920.0,
                "closed_price_min_jpy": 13000,
                "closed_price_avg_jpy": 18500,
                "closed_price_max_jpy": 25000,
                "mercari_bin_avg_jpy": 23500,
                "search_query_jp": "Newニンテンドー3DS LL 本体",
                "source_url": "https://auctions.yahoo.co.jp/search/search?p=New%E3%83%8B%E3%83%B3%E3%83%86%E3%83%B3%E3%83%89%E3%83%BC3DS%20LL",
                "zenmarket_url": "https://zenmarket.jp/pl/yahoo.aspx?q=New%E3%83%8B%E3%83%B3%E3%83%86%E3%83%B3%E3%83%89%E3%83%BC3DS%20LL",
                "buyee_url": "https://buyee.jp/item/search/query/New%E3%83%8B%E3%83%B3%E3%83%86%E3%83%B3%E3%83%89%E3%83%BC3DS%20LL",
                "status": "Aktywna"
            },
            {
                "id": "test_camera",
                "model": "Canon Autoboy 3",
                "color": "Black",
                "platform": "Yahoo! Auctions Japan",
                "category_id": "film_cameras_point_shoot",
                "category_name": "Aparaty Kompaktowe",
                "battery_type": "none",
                "price_jpy": 2500,
                "est_pl_value": 480.0,
                "closed_price_min_jpy": 2500,
                "closed_price_avg_jpy": 3200,
                "closed_price_max_jpy": 3900,
                "search_query_jp": "Canon Autoboy 3",
                "source_url": "https://auctions.yahoo.co.jp/search/search?p=Canon+Autoboy+3",
                "zenmarket_url": "https://zenmarket.jp/pl/yahoo.aspx?q=Canon+Autoboy+3",
                "buyee_url": "https://buyee.jp/item/search/query/Canon+Autoboy+3",
                "status": "Aktywna"
            }
        ]

        self.sample_mercari = [
            {
                "id": "m1234567890",
                "model": "Nintendo DS Lite",
                "color": "Silver",
                "category_id": "nintendo_ds_handhelds",
                "category_name": "Nintendo DS & DSi",
                "battery_type": "li-ion",
                "price_jpy": 2200,
                "price_pln_raw": 54.56,
                "landed_cost_pln": 140.20,
                "est_pl_value": 260.0,
                "est_margin_pln": 119.80,
                "roi_percent": 85.4,
                "status": "Dostępne",
                "condition_badge": "✅ Sprawny"
            },
            {
                "id": "m9999999999",
                "model": "Old Broken Console",
                "status": "Zakończone / 404",
                "price_jpy": 1000
            }
        ]

    def test_process_yahoo_deal(self):
        exporter = WebappExporter(
            rate_jpy=0.024802,
            rate_eur=4.3873,
            is_live_rate=True,
            yahoo_deals=self.sample_yahoo
        )
        processed = exporter.process_yahoo_deal(self.sample_yahoo[0])

        self.assertEqual(processed["id"], "new_n3ds_xl_red")
        self.assertEqual(processed["model"], "New Nintendo 3DS LL (New 3DS XL)")
        self.assertTrue(processed["has_battery"])
        self.assertGreater(processed["landed_cost_pln"], 0)
        self.assertGreater(processed["est_margin_pln"], 0)
        self.assertGreater(processed["max_bid_jpy"], 0)
        self.assertIn("zenmarket_ending_soon", processed["links"])
        self.assertIn("yahoo_closed_archive", processed["links"])

    def test_camera_cap_enforcement(self):
        exporter = WebappExporter(
            rate_jpy=0.024802,
            rate_eur=4.3873,
            is_live_rate=True,
            yahoo_deals=self.sample_yahoo
        )
        cam_deal = exporter.process_yahoo_deal(self.sample_yahoo[1])
        # Camera bid cap in PLN must not exceed MAX_CAMERA_PRICE_PLN (100 PLN)
        max_bid_pln = cam_deal["max_bid_jpy"] * 0.024802
        self.assertLessEqual(max_bid_pln, MAX_CAMERA_PRICE_PLN + 1.0)

    def test_export_file_generation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = Path(tmpdir) / "deals.json"
            exporter = WebappExporter(
                rate_jpy=0.024802,
                rate_eur=4.3873,
                is_live_rate=True,
                mercari_deals=self.sample_mercari,
                yahoo_deals=self.sample_yahoo
            )
            res = exporter.export(output_file=out_file)

            self.assertTrue(out_file.exists())
            with open(out_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.assertIn("meta", data)
            self.assertIn("categories", data)
            self.assertIn("auctions", data)
            self.assertIn("mercari_deals", data)

            self.assertEqual(len(data["auctions"]), 2)
            # Only the 1 active Mercari deal should be included (excluding 404)
            self.assertEqual(len(data["mercari_deals"]), 1)
            self.assertEqual(data["mercari_deals"][0]["id"], "m1234567890")


if __name__ == "__main__":
    unittest.main()
