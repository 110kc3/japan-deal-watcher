import unittest
from pathlib import Path

from watcher.auction_radar import AuctionRadarGenerator, sanitize_md
from watcher.costs import calculate_max_sniper_bid

class TestAuctionRadar(unittest.TestCase):
    def setUp(self):
        self.sample_deals = [
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
                "custom_note": "Sprawny 100%",
                "search_query_jp": "Newニンテンドー3DS LL 本体",
                "source_url": "https://auctions.yahoo.co.jp/search/search?p=New%E3%83%8B%E3%83%B3%E3%83%86%E3%83%B3%E3%83%89%E3%83%BC3DS%20LL",
                "zenmarket_url": "https://zenmarket.jp/pl/yahoo.aspx?q=New%E3%83%8B%E3%83%B3%E3%83%86%E3%83%B3%E3%83%89%E3%83%BC3DS%20LL",
                "buyee_url": "https://buyee.jp/item/search/query/New%E3%83%8B%E3%83%B3%E3%83%86%E3%83%B3%E3%83%89%E3%83%BC3DS%20LL",
                "status": "Aktywna"
            },
            {
                "id": "h1179048211",
                "model": "Hurtowy Pakiet 50 Gier Retro",
                "color": "Mix 50 sztuk",
                "platform": "Yahoo! Auctions Japan",
                "category_id": "retro_games_mix",
                "category_name": "Retro Gry Hurtowe Pakiety",
                "battery_type": "none",
                "price_jpy": 3500,
                "est_pl_value": 750.0,
                "closed_price_min_jpy": 3000,
                "closed_price_avg_jpy": 4800,
                "closed_price_max_jpy": 7500,
                "mercari_bin_avg_jpy": 9500,
                "custom_note": "Zestaw 50 gier retro",
                "search_query_jp": "ゲーム まとめ セット",
                "source_url": "https://auctions.yahoo.co.jp/search/search?p=%E3%82%B2%E3%83%BC%E3%83%A0+%E3%81%BE%E3%81%A8%E3%82%81",
                "zenmarket_url": "https://zenmarket.jp/pl/yahoo.aspx?q=%E3%82%B2%E3%83%BC%E3%83%A0+%E3%81%BE%E3%81%A8%E3%82%81",
                "buyee_url": "https://buyee.jp/item/search/query/%E3%82%B2%E3%83%BC%E3%83%A0+%E3%81%BE%E3%81%A8%E3%82%81",
                "status": "Aktywna"
            }
        ]
        self.sample_timeline = {
            "start_date": "2026-11-07",
            "deadline": "2027-01-06",
            "days_remaining": 58,
            "status_badge": "🟢 Bezpiecznie (58 dni)"
        }

    def test_auction_radar_generation(self):
        gen = AuctionRadarGenerator(
            raw_deals=self.sample_deals,
            timeline_status=self.sample_timeline,
            rate=0.024802,
            rate_eur=4.3873,
            is_live_rate=True
        )
        md = gen.generate()

        self.assertIn("# 📡 Yahoo! Auctions Live Radar", md)
        self.assertIn("Matryca Arbitrażu: Rzeczywiste Ceny Końcowe Yahoo", md)
        self.assertIn("落札相場", md)
        self.assertIn("New Nintendo 3DS LL", md)
        self.assertIn("Hurtowy Pakiet 50 Gier Retro", md)
        self.assertIn("ZenMarket%20Storage", md)
        self.assertIn("Terminal Wyszukiwania Licytacji", md)
        self.assertIn("Praktyczna Instrukcja", md)
        self.assertIn("Kończące się", md)
        self.assertIn("Od 1 JPY", md)

    def test_sanitize_md(self):
        self.assertEqual(sanitize_md(None), "")
        self.assertEqual(sanitize_md("Text | with | pipes"), "Text &#124; with &#124; pipes")
        self.assertEqual(sanitize_md("Multi\nline\rtext"), "Multi line text")

if __name__ == "__main__":
    unittest.main()
