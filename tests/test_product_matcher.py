"""Unit tests for ProductMatcher and regression tests for F01 mismatch cases."""

import unittest
from watcher.product_matcher import ProductMatcher, ProductMatchResult


class TestProductMatcher(unittest.TestCase):
    """Verifies that the 5 documented F01 mismatches and other misleading listings are rejected."""

    def test_f01_m50999156610_ps4_games_rejected_as_console(self):
        target = {
            "id": "m50999156610",
            "model": "PlayStation 4 Metal Gear Solid V Limited Edition (Boxed)",
            "category_id": "high_margin_curated_consoles"
        }
        listing = {
            "id": "m50999156610",
            "title": "[まとめ売り] PS4 メタルギアソリッドV 2本セット",
            "category_id": "high_margin_curated_consoles"
        }
        res = ProductMatcher.verify_deal(target, listing)
        self.assertFalse(res.is_match, "PS4 software bundle must not match PS4 limited console")
        self.assertIn("gier", res.reason.lower())

    def test_f01_m21968455105_mju_zoom_rejected_as_mju2_prime(self):
        target = {
            "id": "m21968455105",
            "model": "Olympus [mju:]-II (μ-II 35mm f/2.8 Prime - Czarny Weatherproof)",
            "category_id": "film_cameras_point_shoot"
        }
        listing = {
            "id": "m21968455105",
            "title": "オリンパス ミュー(mju:)ZOOM PANORAMA",
            "category_id": "film_cameras_point_shoot"
        }
        res = ProductMatcher.verify_deal(target, listing)
        self.assertFalse(res.is_match, "Mju Zoom must not match rare Mju-II 35mm f/2.8 Prime")
        self.assertIn("zoom", res.reason.lower())

    def test_f01_m63811160268_ds_lite_silicone_cover_rejected(self):
        target = {
            "id": "m63811160268",
            "model": "Nintendo DS Lite Pokémon Dialga & Palkia Edition",
            "category_id": "nintendo_ds_handhelds"
        }
        listing = {
            "id": "m63811160268",
            "title": "Nintendo DS Liteシリコンカバー ディアルガ パルキア ダークライ",
            "category_id": "nintendo_ds_handhelds"
        }
        res = ProductMatcher.verify_deal(target, listing)
        self.assertFalse(res.is_match, "Silicone cover must not match DS Lite console")
        self.assertIn("pokrowiec", res.reason.lower())

    def test_f01_m35606738599_asics_shoes_rejected_as_psp(self):
        target = {
            "id": "m35606738599",
            "model": "PSP-2000 Mint Green",
            "category_id": "psp_handheld"
        }
        listing = {
            "id": "m35606738599",
            "title": "22.0 ASICS SUKU2 (スクスク) TOPSPEED MINI",
            "category_id": "psp_handheld"
        }
        res = ProductMatcher.verify_deal(target, listing)
        self.assertFalse(res.is_match, "Shoes must not match PSP console")
        self.assertIn("obuwniczy", res.reason.lower())

    def test_f01_m88450883898_outer_box_and_manual_rejected(self):
        target = {
            "id": "m88450883898",
            "model": "Game Boy Advance SP (AGS-001) Komplet",
            "category_id": "gameboy_advance_retro"
        }
        listing = {
            "id": "m88450883898",
            "title": "ゲームボーイアドバンスSP 外箱 取扱説明書 オニキスブラック",
            "category_id": "gameboy_advance_retro"
        }
        res = ProductMatcher.verify_deal(target, listing)
        self.assertFalse(res.is_match, "Box and manual without console must not match GBA SP console")
        self.assertTrue("pudełko" in res.reason.lower() or "instrukcj" in res.reason.lower() or "brak konsoli" in res.reason.lower())

    def test_valid_console_matches_successfully(self):
        target = {
            "id": "m1122334455",
            "model": "Nintendo 3DS",
            "category_id": "nintendo_3ds_handhelds"
        }
        listing = {
            "id": "m1122334455",
            "title": "ニンテンドー3DS コスモブラック 本体 充電器付き 完動品",
            "category_id": "nintendo_3ds_handhelds"
        }
        res = ProductMatcher.verify_deal(target, listing)
        self.assertTrue(res.is_match)

    def test_valid_prime_lens_matches_successfully(self):
        target = {
            "id": "m9988776655",
            "model": "Olympus [mju:]-II (μ-II 35mm f/2.8 Prime - Czarny Weatherproof)",
            "category_id": "film_cameras_point_shoot"
        }
        listing = {
            "id": "m9988776655",
            "title": "OLYMPUS μ [mju:]-II 35mm F2.8 単焦点 ブラック 動作確認済み",
            "category_id": "film_cameras_point_shoot"
        }
        res = ProductMatcher.verify_deal(target, listing)
        self.assertTrue(res.is_match)

    def test_pc35af_m_motorized_rejected_when_manual_desired(self):
        target = {
            "id": "m4455667788",
            "model": "Pentax PC35AF (Manual Thumbwheel 35mm f/2.8)",
            "category_id": "film_cameras_point_shoot"
        }
        listing = {
            "id": "m4455667788",
            "title": "PENTAX PC35AF-M オートフォーカス フィルムカメラ",
            "category_id": "film_cameras_point_shoot"
        }
        res = ProductMatcher.verify_deal(target, listing)
        self.assertFalse(res.is_match)
        self.assertIn("pc35af-m", res.reason.lower())


if __name__ == "__main__":
    unittest.main()
