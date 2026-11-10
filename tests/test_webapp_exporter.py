import json
import tempfile
import unittest
from pathlib import Path

from watcher.webapp_exporter import WebappExporter, clean_polish_market_queries
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
        self.assertIn("primary_url", processed["links"])
        self.assertIn("zenmarket_ending_soon", processed["links"])
        self.assertIn("yahoo_closed_archive", processed["links"])
        self.assertIn("time_remaining_minutes", processed)
        self.assertIn("time_remaining_formatted", processed)
        self.assertIn("price_stage_note", processed)
        self.assertIn("predicted_closure_jpy", processed)
        self.assertIn("condition_grade", processed)
        self.assertIn("verdict_label", processed)
        self.assertIn("recommendation_text", processed)

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
            self.assertIn("search_streams", data)

            self.assertEqual(len(data["auctions"]), 2)
            # Only the 1 active Mercari deal should be included (excluding 404)
            self.assertEqual(len(data["mercari_deals"]), 1)
            self.assertEqual(data["mercari_deals"][0]["id"], "m1234567890")
            self.assertGreaterEqual(len(data["search_streams"]), 20)

    def test_specific_auction_links_and_search_streams(self):
        """Ensures auctions link directly to specific auction listings, and search streams provide price guides."""
        auction_item = {
            "id": "v1173928104",
            "auction_id": "v1173928104",
            "model": "PCH-2000 Slim",
            "platform": "Yahoo! Auctions Japan",
            "category_id": "ps_vita",
            "category_name": "PlayStation Vita",
            "battery_type": "li-ion",
            "price_jpy": 10200,
            "est_pl_value": 650.0,
            "search_query_jp": "PSヴィータ PCH-2000 本体",
            "status": "Aktywna"
        }
        exporter = WebappExporter(
            rate_jpy=0.024802,
            rate_eur=4.3873,
            is_live_rate=True,
            yahoo_deals=[auction_item]
        )
        processed = exporter.process_yahoo_deal(auction_item)
        links = processed["links"]

        # Ensure direct auction links, not general searches
        self.assertEqual(links["primary_url"], "https://zenmarket.jp/pl/auction.aspx?itemCode=v1173928104")
        self.assertEqual(links["zenmarket_sniper"], "https://zenmarket.jp/pl/auction.aspx?itemCode=v1173928104")
        self.assertEqual(links["yahoo_direct"], "https://page.auctions.yahoo.co.jp/jp/auction/v1173928104")
        self.assertEqual(links["buyee_url"], "https://buyee.jp/item/yahoo/auction/v1173928104")

        # Stream auxiliary links
        self.assertIn("sort=end&order=asc", links["zenmarket_ending_soon"])
        self.assertIn("sort=price&order=asc", links["zenmarket_lowest_bid"])
        self.assertIn("closedsearch", links["yahoo_closed_archive"])

    def test_clean_polish_market_queries(self):
        cases = [
            ("【断捨離】Karton 50 Gier Nintendo DS & 3DS (Likwidacja Pokoju / Wyprzedaż)", "gry nintendo ds zestaw", "gry-nintendo-ds-zestaw"),
            ("【実家整理】Karton 40 Kartridży Game Boy & GBA (Strych / Pamiątki z Dzieciństwa)", "gry game boy advance zestaw", "gry-game-boy-advance-zestaw"),
            ("【引退品】Zestaw 60 Gier Sony PSP UMD (Kolekcja Gracza / まとめ売り)", "gry psp zestaw", "gry-psp-zestaw"),
            ("【断捨離】Zestaw 15 Kartridży Pokémon (DS / GBA / GBC - Wyprzedaż Prywatna)", "gry pokemon nintendo", "gry-pokemon-nintendo"),
            ("Olympus [mju:]-II (μ-II 35mm f/2.8 Prime - Czarny Weatherproof)", "Olympus Mju II", "olympus-mju-ii"),
            ("Pentax PC35AF (Oryginalny Naciąg Ręczny Thumbwheel - Bez silnika M)", "Pentax PC35AF", "pentax-pc35af"),
            ("PCH-2000 Slim", "PS Vita Slim", "ps-vita-slim"),
            ("PCH-1000 OLED", "PS Vita OLED", "ps-vita-oled"),
            ("New Nintendo 3DS LL (New 3DS XL)", "New Nintendo 3DS XL", "new-nintendo-3ds-xl"),
            ("DualSense Wireless Controller (Astro Bot Limited Edition)", "DualSense Astro Bot", "dualsense-astro-bot"),
            ("DualShock 4 Berry Blue Limited Edition", "DualShock 4 Berry Blue", "dualshock-4-berry-blue")
        ]
        for model_str, expected_pl_q, expected_slug in cases:
            pl_q, slug = clean_polish_market_queries({"model": model_str})
            self.assertEqual(pl_q, expected_pl_q)
            self.assertEqual(slug, expected_slug)
            self.assertNotIn("%26", slug)
            self.assertNotIn("&", slug)
            self.assertRegex(slug, r"^[a-z0-9-]+$")

    def test_proxy_id_leak_prevention(self):
        proxy_item = {
            "id": "danshari_ds_3ds_50",
            "model": "【断捨離】Karton 50 Gier Nintendo DS & 3DS (Likwidacja Pokoju / Wyprzedaż)",
            "status": "Dostępne",
            "search_query_jp": "DS 3DS ソフト 断捨離 大量 まとめ売り",
            "target_price_jpy": 4800,
            "est_pl_value": 380.0
        }
        exporter = WebappExporter(
            rate_jpy=0.024802,
            rate_eur=4.3873,
            is_live_rate=True,
            mercari_deals=[proxy_item]
        )
        processed = exporter.process_mercari_deal(proxy_item)
        links = processed["links"]

        # Ensure no URL contains the raw string 'danshari_ds_3ds_50'
        for link_name, url in links.items():
            self.assertNotIn("danshari_ds_3ds_50", url, f"Link {link_name} leaked internal proxy ID")

        # Verify search query stream presence
        self.assertIn("primary_url", links)
        self.assertIn("zenmarket_search_mercari", links)
        self.assertIn("mercari_live_search", links)
        self.assertIn("zenmarket_yahoo_search", links)
        self.assertIn("allegro_search", links)
        self.assertIn("olx_search", links)
        self.assertEqual(links["olx_search"], "https://www.olx.pl/oferty/q-gry-nintendo-ds-zestaw/")

    def test_auctions_sorted_by_remaining_time_ascending(self):
        """Verifies that exported auctions are pre-sorted by remaining time ascending (least time first)."""
        deals = [
            {"id": "deal_3", "model": "Deal 3", "price_jpy": 3000, "est_pl_value": 300, "time_remaining_minutes": 1400},
            {"id": "deal_1", "model": "Deal 1", "price_jpy": 1000, "est_pl_value": 300, "time_remaining_minutes": 18},
            {"id": "deal_2", "model": "Deal 2", "price_jpy": 2000, "est_pl_value": 300, "time_remaining_minutes": 95},
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = Path(tmpdir) / "deals.json"
            exporter = WebappExporter(
                rate_jpy=0.024802,
                rate_eur=4.3873,
                is_live_rate=True,
                yahoo_deals=deals
            )
            exporter.export(output_file=out_file)
            with open(out_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            auctions = data["auctions"]
            self.assertEqual(len(auctions), 3)
            self.assertEqual(auctions[0]["id"], "deal_1")
            self.assertEqual(auctions[0]["time_remaining_minutes"], 18)
            self.assertEqual(auctions[1]["id"], "deal_2")
            self.assertEqual(auctions[1]["time_remaining_minutes"], 95)
            self.assertEqual(auctions[2]["id"], "deal_3")
            self.assertEqual(auctions[2]["time_remaining_minutes"], 1400)


if __name__ == "__main__":
    unittest.main()
