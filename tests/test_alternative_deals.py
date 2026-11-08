import json
import unittest
from pathlib import Path

from watcher.config import YAHOO_DEALS_FILE, BASE_DIR
from watcher.alternative_generator import AlternativeDealsGenerator, sanitize_md

class TestAlternativeDeals(unittest.TestCase):
    def setUp(self):
        self.sample_deals = [
            {
                "id": "yahoo_psvita_001",
                "model": "Sony PlayStation Vita PCH-2000 (Aqua Blue)",
                "color": "Aqua Blue",
                "platform": "Yahoo! Auctions",
                "category_id": "ps_vita",
                "category_name": "PlayStation Vita (OLED / Slim)",
                "battery_type": "li-ion",
                "price_jpy": 12500,
                "est_pl_value": 750.0,
                "custom_note": "Aukcja od 1 JPY, stan B+",
                "source_url": "https://auctions.yahoo.co.jp/jp/auction/yahoo_psvita_001",
                "zenmarket_url": "https://zenmarket.jp/pl/auction.aspx?itemCode=yahoo_psvita_001",
                "buyee_url": "https://buyee.jp/item/yahoo/auction/yahoo_psvita_001",
                "status": "Aktywna (Licytacja)"
            },
            {
                "id": "surugaya_psp_games_001",
                "model": "Lot 40 gier PSP UMD (Monster Hunter, Final Fantasy, Tekken)",
                "color": "Mix 40 sztuk",
                "platform": "Surugaya",
                "category_id": "psp_games_mix",
                "category_name": "Retro PSP UMD Hurtowe Pakiety (0% Baterii)",
                "battery_type": "no-battery",
                "price_jpy": 3800,
                "est_pl_value": 480.0,
                "custom_note": "Zestaw 40 płyt UMD, stan pudełek dobry",
                "source_url": "https://www.suruga-ya.jp/product/detail/surugaya_psp_games_001",
                "zenmarket_url": "https://zenmarket.jp/pl/otherproduct.aspx?itemCode=surugaya_psp_games_001",
                "buyee_url": "https://buyee.jp/item/surugaya/surugaya_psp_games_001",
                "status": "Dostępne w sklepie"
            }
        ]
        self.sample_timeline = {
            "start_date": "2026-11-07",
            "deadline": "2027-01-06",
            "days_passed": 1,
            "days_remaining": 59,
            "status_badge": "🟢 Bezpiecznie (59 dni)",
            "status_color": "brightgreen"
        }

    def test_recompute_costs(self):
        from watcher.costs import calculate_landed_cost
        rate = 0.024832
        rate_eur = 4.35
        gen = AlternativeDealsGenerator(
            raw_deals=self.sample_deals,
            timeline_status=self.sample_timeline,
            rate=rate,
            rate_eur=rate_eur,
            is_live_rate=True
        )
        deals = gen.deals
        self.assertEqual(len(deals), 2)

        # Item 1: PS Vita (12500 JPY, 800 JPY dom, 2 EUR fee, 3.5% dep, 23% VAT)
        d1 = deals[0]
        c1 = calculate_landed_cost(12500, "ps_vita", rate_jpy=rate, rate_eur=rate_eur)
        self.assertEqual(d1["price_pln_raw"], c1["price_pln_raw"])
        self.assertEqual(d1["landed_cost_pln"], c1["landed_cost_pln"])
        self.assertEqual(d1["est_margin_pln"], round(750.0 - c1["landed_cost_pln"], 2))
        self.assertGreater(d1["roi_percent"], 0)

        # Item 2: PSP games mix (3800 JPY, 800 JPY dom, 2 EUR fee, 3.5% dep, 23% VAT)
        d2 = deals[1]
        c2 = calculate_landed_cost(3800, "psp_games_mix", rate_jpy=rate, rate_eur=rate_eur)
        self.assertEqual(d2["landed_cost_pln"], c2["landed_cost_pln"])
        self.assertGreater(d2["est_margin_pln"], 200)

    def test_markdown_generation_content(self):
        gen = AlternativeDealsGenerator(
            raw_deals=self.sample_deals,
            timeline_status=self.sample_timeline,
            rate=0.024832,
            is_live_rate=True
        )
        md = gen.generate()

        self.assertIn("# 🔨 Yahoo! Auctions Japan & Alternative Deals Dashboard", md)
        self.assertIn("NBP%20Live", md)
        self.assertIn("Automated Sniper", md)
        self.assertIn("Wróć do Głównego Dashboardu Mercari (README.md)", md)
        self.assertIn("Porównanie Japońskich Platform Zakupowych", md)
        self.assertIn("Surugaya (駿河屋)", md)
        self.assertIn("Top 3 Rekomendowane Perełki", md)
        self.assertIn("Optymalny Koszyk Konsolidacyjny", md)
        self.assertIn("Poradnik Licytacji przez ZenMarket Sniper", md)
        self.assertIn("Aqua Blue", md)
        self.assertIn("Lot 40 gier PSP UMD", md)

    def test_yahoo_deals_json_integrity(self):
        self.assertTrue(YAHOO_DEALS_FILE.exists(), f"Missing {YAHOO_DEALS_FILE}")
        with open(YAHOO_DEALS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 25, "Expected at least 25 alternative deals")

        required_keys = {
            "id", "model", "platform", "category_id", "category_name",
            "battery_type", "price_jpy", "est_pl_value", "source_url",
            "zenmarket_url", "buyee_url", "status"
        }

        platforms = set()
        categories = set()
        for deal in data:
            for k in required_keys:
                self.assertIn(k, deal, f"Missing key {k} in item {deal.get('id')}")
            self.assertGreater(deal["price_jpy"], 0)
            self.assertGreater(deal["est_pl_value"], 0)
            self.assertTrue(deal["source_url"].startswith("http"))
            self.assertTrue(deal["zenmarket_url"].startswith("http"))
            platforms.add(deal["platform"])
            categories.add(deal["category_id"])

        self.assertIn("Yahoo! Auctions Japan", platforms)
        self.assertIn("Surugaya", platforms)
        self.assertGreaterEqual(len(categories), 8, "Expected diverse category coverage")

if __name__ == "__main__":
    unittest.main()
