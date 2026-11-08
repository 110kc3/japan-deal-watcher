import unittest
from pathlib import Path

from watcher.sniper_guide_generator import SniperGuideGenerator, sanitize_md
from watcher.costs import calculate_max_sniper_bid

class TestSniperGuide(unittest.TestCase):
    def setUp(self):
        self.sample_deals = [
            {
                "id": "yahoo_psvita_001",
                "model": "Sony PlayStation Vita PCH-2000 (Aqua Blue)",
                "color": "Aqua Blue",
                "platform": "Yahoo! Auctions Japan",
                "category_id": "ps_vita",
                "category_name": "PlayStation Vita (OLED / Slim)",
                "battery_type": "li-ion",
                "price_jpy": 13500,
                "est_pl_value": 890.0,
                "custom_note": "Sprawny 100%",
                "search_query_jp": "PS Vita PCH-2000 アクアブルー",
                "source_url": "https://auctions.yahoo.co.jp/search/search?p=PS+Vita+PCH-2000",
                "zenmarket_url": "https://zenmarket.jp/pl/yahoo.aspx?q=PS+Vita+PCH-2000",
                "buyee_url": "https://buyee.jp/item/search/query/PS+Vita+PCH-2000",
                "status": "Aktywna"
            },
            {
                "id": "surugaya_psp_games_001",
                "model": "Hurtowy Pakiet 50 Gier PSP UMD",
                "color": "Mix 50 sztuk",
                "platform": "Yahoo! Auctions Japan",
                "category_id": "psp_games_mix",
                "category_name": "Retro PSP UMD Hurtowe Pakiety (0% Baterii)",
                "battery_type": "no-battery",
                "price_jpy": 4200,
                "est_pl_value": 950.0,
                "custom_note": "Zestaw 50 płyt UMD",
                "search_query_jp": "PSP ソフト まとめ 大量",
                "source_url": "https://auctions.yahoo.co.jp/search/search?p=PSP+ソフト",
                "zenmarket_url": "https://zenmarket.jp/pl/yahoo.aspx?q=PSP+ソフト",
                "buyee_url": "https://buyee.jp/item/search/query/PSP+ソフト",
                "status": "Aktywna"
            }
        ]
        self.sample_timeline = {
            "start_date": "2026-11-07",
            "deadline": "2027-01-06",
            "days_remaining": 59,
            "status_badge": "🟢 Bezpiecznie (59 dni)"
        }

    def test_sniper_guide_generation(self):
        gen = SniperGuideGenerator(
            raw_deals=self.sample_deals,
            timeline_status=self.sample_timeline,
            rate=0.024832,
            rate_eur=4.3925,
            is_live_rate=True
        )
        md = gen.generate()

        self.assertIn("# 🎯 Yahoo! Auctions Sniping Masterclass & Real Closing Price Guide", md)
        self.assertIn("Anatomia Ostatnich 15 Minut Aukcji", md)
        self.assertIn("Tabela Twardych Limitów Snajpera", md)
        self.assertIn("Złote Okna Czasowe", md)
        self.assertIn("Czarna Lista i Pułapki Sprzedawców", md)
        self.assertIn("Multi-Sniper na 1 Budżet", md)
        self.assertIn("Tajniki Logistyki Bateryjnej: Czy na pewno nie da się wysłać więcej niż 2 baterie?", md)
        self.assertIn("Poczta Morska (Japan Post Seamail", md)
        self.assertIn("Dry Shipping", md)
        self.assertIn("Szybka Checklista Przed Wciśnięciem „Snajper”", md)

        # Check ending soon URLs
        self.assertIn("sort=end&order=asc", md)
        self.assertIn("sort=end&order=a", md)
        self.assertIn("closedsearch", md)
        self.assertIn("aucfan.com", md)

        # Check items in table
        self.assertIn("Sony PlayStation Vita PCH-2000 (Aqua Blue)", md)
        self.assertIn("Hurtowy Pakiet 50 Gier PSP UMD", md)
        self.assertIn("🔴 1 Li-Ion", md)
        self.assertIn("🟢 0% Li-Ion", md)

    def test_sniper_lens_cap_enforcement(self):
        lens_deals = [
            {
                "id": "yahoo_lens_001",
                "model": "SMC Pentax-M 50mm f/1.4",
                "color": "Black",
                "platform": "Yahoo! Auctions Japan",
                "category_id": "analog_lenses",
                "category_name": "Obiektywy Analogowe (0% Baterii)",
                "battery_type": "none",
                "price_jpy": 2800,
                "est_pl_value": 380.0,
                "custom_note": "Optyka czysta",
                "search_query_jp": "SMC Pentax-M 50mm",
                "source_url": "https://auctions.yahoo.co.jp/search",
                "zenmarket_url": "https://zenmarket.jp",
                "status": "Aktywna"
            }
        ]
        gen = SniperGuideGenerator(
            raw_deals=lens_deals,
            timeline_status=self.sample_timeline,
            rate=0.024832,
            rate_eur=4.3925,
            is_live_rate=True
        )
        md = gen.generate()
        # Max lens price is 100 PLN -> 100 / 0.024832 = 4027 JPY -> rounded to 4,000 JPY
        self.assertIn("4,000 JPY", md)

    def test_calculate_max_sniper_bid_logic(self):
        cap = calculate_max_sniper_bid(890.0, "ps_vita", target_roi_pct=30.0, rate_jpy=0.024832, rate_eur=4.3925)
        self.assertGreater(cap["max_bid_jpy"], 15000)
        self.assertGreaterEqual(cap["guaranteed_roi_pct"], 30.0)
        self.assertGreater(cap["guaranteed_margin_pln"], 200.0)

if __name__ == "__main__":
    unittest.main()
