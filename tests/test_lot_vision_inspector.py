"""Unit tests for LotVisionInspector and MysteryLotsGenerator."""

import unittest
from watcher.lot_vision_inspector import LotVisionInspector, RETRO_GAME_KNOWLEDGE_BASE, DANSHARI_KEYWORDS
from watcher.mystery_lots_generator import MysteryLotsGenerator


class TestLotVisionInspector(unittest.TestCase):
    def test_detect_danshari_keywords(self):
        t1 = "【断捨離】ニンテンドーDS ゲームソフト 大量まとめ売り"
        res1 = LotVisionInspector.detect_danshari_type(t1)
        self.assertTrue(res1["is_mystery_lot"])
        self.assertEqual(res1["lot_type"], "danshari_purge")
        self.assertIn("Danshari", res1["label"])

        t2 = "【実家整理】古いゲームボーイアドバンス ソフト 処分"
        res2 = LotVisionInspector.detect_danshari_type(t2)
        self.assertTrue(res2["is_mystery_lot"])
        self.assertIn(res2["lot_type"], ["attic_parental_home", "clearance_liquidation"])

        t3 = "Sony PlayStation Vita PCH-2000 Aqua Blue Console"
        res3 = LotVisionInspector.detect_danshari_type(t3)
        self.assertFalse(res3["is_mystery_lot"])

    def test_retro_game_identification(self):
        sample_deal = {
            "model": "【断捨離】DS 3DS ゲームソフト 45本 ポケットモンスター ハートゴールド プラチナ ゼルダの伝説 夢幻の砂時計",
            "custom_note": "Aukcja wyprzedażowa z pudłem gier retro",
            "price_jpy": 4500,
            "est_pl_value": 650.0
        }
        inspection = LotVisionInspector.inspect_lot_photo_contents(sample_deal)

        self.assertTrue(inspection["inspected"])
        self.assertEqual(inspection["total_items_spotted"], 45)
        gems = inspection["top_gems"]
        self.assertGreaterEqual(len(gems), 3)

        titles = [g["title"] for g in gems]
        self.assertTrue(any("HeartGold" in t for t in titles))
        self.assertTrue(any("Platinum" in t for t in titles))
        self.assertTrue(any("Zelda" in t for t in titles))

        self.assertGreater(inspection["spotted_gems_value_pln"], 180.0)
        self.assertIn("Break-Even", inspection["break_even_gem"])
        self.assertFalse(inspection["battery_hazard_detected"])

    def test_battery_hazard_detection(self):
        deal_with_console = {
            "model": "【実家整理】DS Lite本体 + ゲームソフト 30本まとめ売り",
            "custom_note": "Konsola z grami w jednym pudle",
            "price_jpy": 3500,
            "est_pl_value": 400.0
        }
        inspection = LotVisionInspector.inspect_lot_photo_contents(deal_with_console)
        self.assertTrue(inspection["battery_hazard_detected"])
        self.assertIn("Dry Shipping", inspection["battery_notes"])

    def test_format_inspection_markdown(self):
        inspection = {
            "inspected": True,
            "inspection_badge": "🔍 Inspekcja Zdjęcia (AI Vision)",
            "total_items_spotted": 40,
            "lot_type": "danshari_purge",
            "lot_type_name": "Danshari (Minimalistyczne Czyszczenie Domu)",
            "battery_notes": "🟢 100% Czyste Gry (0% Li-Ion)",
            "break_even_gem": "Sam Pokémon Emerald (210 zł) pokrywa 100% ceny kartonu!",
            "top_gems": [
                {
                    "title": "Pokémon Emerald (GBA)",
                    "platform": "Game Boy Advance",
                    "rarity": "⭐⭐⭐⭐⭐ Top Skarb",
                    "est_pl_value": 210.0,
                    "allegro_archive_pln": 240.0,
                    "olx_haggled_pln": 190.0
                }
            ]
        }
        md = LotVisionInspector.format_inspection_markdown(inspection)
        self.assertIn("Inspekcja Zdjęcia", md)
        self.assertIn("Break-Even", md)
        self.assertIn("Pokémon Emerald (GBA)", md)
        self.assertIn("210 zł", md)

    def test_mystery_lots_generator(self):
        sample_deals = [
            {
                "id": "danshari_test_001",
                "platform": "Yahoo! Auctions Japan",
                "category_id": "danshari_mystery_lots",
                "category_name": "Pakiety Różności i Likwidacje Kolekcji",
                "model": "【断捨離】DS 3DS ゲームソフト 50本まとめ売り",
                "color": "Mix",
                "price_jpy": 4500,
                "est_pl_value": 650.0,
                "allegro_archive_pln": 720.0,
                "olx_haggled_pln": 590.0,
                "battery_type": "none",
                "image_url": "./assets/images/mystery_lot.svg",
                "search_query_jp": "DS 3DS ソフト 断捨離 大量",
                "photo_inspection": {
                    "inspected": True,
                    "total_items_spotted": 50,
                    "lot_type_name": "Danshari",
                    "battery_notes": "🟢 0% Li-Ion",
                    "top_gems": [
                        {"title": "Pokémon HeartGold", "est_pl_value": 240.0}
                    ]
                }
            }
        ]
        timeline = {"days_remaining": 58, "start_date": "2026-11-07", "deadline": "2027-01-06"}
        gen = MysteryLotsGenerator(
            raw_deals=sample_deals,
            timeline_status=timeline,
            rate=0.024802,
            is_live_rate=True
        )
        md = gen.generate()

        self.assertIn("# 📦 Pakiety Różności, Danshari i Skarby w Kartonach", md)
        self.assertIn("Pokémon HeartGold", md)
        self.assertIn("0% Li-Ion", md)
        self.assertIn("Snajper ZenMarket", md)
        self.assertIn("closedsearch", md)
        self.assertIn("aucfan.com", md)


if __name__ == "__main__":
    unittest.main()
