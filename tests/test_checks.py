"""Unit tests for watcher.checks module and system verification audit."""

import unittest
from watcher.checks import (
    check_camera_price_cap,
    check_lens_price_cap,
    check_defects,
    check_untested_opportunity,
    check_shipping_trap,
    check_iata_lithium,
    check_profitability_hurdle,
    check_currency_health,
    check_dataset_integrity,
    check_markdown_dashboards,
    run_full_system_audit,
    is_camera_item,
    is_lens_item,
    is_nintendo_ds_item,
)
from watcher.config import WATCHLIST_FILE, YAHOO_DEALS_FILE, BASE_DIR, MAX_CAMERA_PRICE_PLN, MAX_LENS_PRICE_PLN


class TestChecks(unittest.TestCase):

    def test_camera_detection(self):
        cam1 = {"category_id": "film_cameras_point_shoot", "model": "Point & Shoot"}
        cam2 = {"category_id": "other", "category_name": "Aparaty Analogowe Typu Małpka"}
        cam3 = {"category_id": "other", "model": "Canon Autoboy 3"}
        cam4 = {"category_id": "other", "model": "Olympus μ [mju:]"}
        not_cam = {"category_id": "ps_vita", "model": "PCH-2000 Slim"}

        self.assertTrue(is_camera_item(cam1))
        self.assertTrue(is_camera_item(cam2))
        self.assertTrue(is_camera_item(cam3))
        self.assertTrue(is_camera_item(cam4))
        self.assertFalse(is_camera_item(not_cam))

    def test_lens_detection(self):
        lens1 = {"category_id": "analog_lenses", "model": "SMC Pentax-M 50mm f/1.4"}
        lens2 = {"category_id": "other", "category_name": "Obiektywy Analogowe"}
        lens3 = {"category_id": "other", "model": "Olympus F.Zuiko Auto-S 50mm f/1.8"}
        lens4 = {"category_id": "other", "model": "Super Takumar 55mm f/1.8 Lens"}
        not_lens = {"category_id": "nintendo_ds_consoles", "model": "Nintendo DS Lite"}

        self.assertTrue(is_lens_item(lens1))
        self.assertTrue(is_lens_item(lens2))
        self.assertTrue(is_lens_item(lens3))
        self.assertTrue(is_lens_item(lens4))
        self.assertFalse(is_lens_item(not_lens))

    def test_nintendo_ds_detection(self):
        ds1 = {"category_id": "nintendo_ds_consoles", "model": "Nintendo DS Lite"}
        ds2 = {"category_id": "other", "category_name": "Nintendo DS / DSi / 3DS"}
        ds3 = {"category_id": "other", "model": "Nintendo DSi LL Dark Brown IPS"}
        ds4 = {"category_id": "other", "model": "Nintendo 3DS XL Aqua Blue"}
        not_ds = {"category_id": "ps_vita", "model": "PlayStation Vita"}

        self.assertTrue(is_nintendo_ds_item(ds1))
        self.assertTrue(is_nintendo_ds_item(ds2))
        self.assertTrue(is_nintendo_ds_item(ds3))
        self.assertTrue(is_nintendo_ds_item(ds4))
        self.assertFalse(is_nintendo_ds_item(not_ds))

    def test_camera_price_cap_rule(self):
        # 1. Camera <= 100 PLN passes
        cheap_camera = {
            "category_id": "film_cameras_point_shoot",
            "model": "Minolta Riva Zoom",
            "price_pln_raw": 37.50
        }
        ok, msg = check_camera_price_cap(cheap_camera)
        self.assertTrue(ok)
        self.assertIn("mieści się w limicie", msg)

        # 2. Camera > 100 PLN fails
        expensive_camera = {
            "category_id": "film_cameras_point_shoot",
            "model": "Olympus mju II",
            "price_pln_raw": 198.00
        }
        ok, msg = check_camera_price_cap(expensive_camera)
        self.assertFalse(ok)
        self.assertIn("przekracza dopuszczalny limit", msg)
        self.assertIn("Aparaty powyżej 100 zł nie są okazjami", msg)

        # 3. Non-camera item > 100 PLN is not affected
        expensive_console = {
            "category_id": "ps_vita",
            "model": "PS Vita OLED",
            "price_pln_raw": 450.00
        }
        ok, msg = check_camera_price_cap(expensive_console)
        self.assertTrue(ok)
        self.assertIn("N/A", msg)

    def test_lens_price_cap_rule(self):
        # 1. Lens <= 100 PLN passes
        cheap_lens = {
            "category_id": "analog_lenses",
            "model": "SMC Pentax-M 50mm f/2",
            "price_pln_raw": 44.70
        }
        ok, msg = check_lens_price_cap(cheap_lens)
        self.assertTrue(ok)
        self.assertIn("mieści się w limicie", msg)

        # 2. Lens > 100 PLN fails
        expensive_lens = {
            "category_id": "analog_lenses",
            "model": "Canon FD 50mm f/1.4",
            "price_pln_raw": 215.00
        }
        ok, msg = check_lens_price_cap(expensive_lens)
        self.assertFalse(ok)
        self.assertIn("przekracza dopuszczalny limit", msg)
        self.assertIn("Obiektywy w dużych cenach odpadają", msg)

        # 3. Non-lens item > 100 PLN is not affected
        expensive_console = {
            "category_id": "ps_vita",
            "model": "PS Vita OLED",
            "price_pln_raw": 450.00
        }
        ok, msg = check_lens_price_cap(expensive_console)
        self.assertTrue(ok)
        self.assertIn("N/A", msg)

    def test_expanded_defects_detection(self):
        # Optics defects: fungus, haze
        ok, msg = check_defects("レンズにカビあり。撮影に影響します。")
        self.assertFalse(ok)
        self.assertIn("カビあり", msg)

        ok, msg = check_defects("光学はクモリあり。撮影に支障します。")
        self.assertFalse(ok)
        self.assertIn("クモリあり", msg)

        # Mechanics defects: shutter stuck, winder broken
        ok, msg = check_defects("シャッター不動のためジャンクです。")
        self.assertFalse(ok)
        self.assertIn("シャッター不動", msg)

        # Corrosion: blue verdigris, terminal acid
        ok, msg = check_defects("電池室に青サビがあります。")
        self.assertFalse(ok)
        self.assertIn("青サビ", msg)

        # Hinge & battery door broken
        ok, msg = check_defects("ヒンジ破損により画面が自立しません。")
        self.assertFalse(ok)
        self.assertIn("ヒンジ破損", msg)

        # Stick drift
        ok, msg = check_defects("左スティックドリフトが発生しています。")
        self.assertFalse(ok)
        self.assertIn("ドリフト", msg)

        # Clean negations pass
        ok, msg = check_defects("カビなし、クモリなし、動作確認済みです。")
        self.assertTrue(ok)
        self.assertEqual(msg, "Brak uszkodzeń i defektów")

    def test_trap_keywords_detection(self):
        # Empty box trap
        ok, msg = check_defects("PlayStation 5 DualSense 箱のみです。本体はありません。")
        self.assertFalse(ok)
        self.assertIn("箱のみ", msg)

        # Manual only trap
        ok, msg = check_defects("取説のみ。説明書のみの出品です。")
        self.assertFalse(ok)
        self.assertIn("説明書のみ", msg)

    def test_untested_opportunity_detection(self):
        ok, msg = check_untested_opportunity("電源コード欠品のため動作未確認です。現状渡し。")
        self.assertTrue(ok)
        self.assertIn("動作未確認", msg)

        ok, msg = check_untested_opportunity("実家から出てきたものです。動作未チェック。")
        self.assertTrue(ok)
        self.assertIn("実家から出てきた", msg)

        ok, msg = check_untested_opportunity("動作確認済み、完動品です。")
        self.assertFalse(ok)

    def test_domestic_shipping_trap(self):
        ok, msg = check_shipping_trap("全国送料無料でお届けします。")
        self.assertTrue(ok)
        self.assertIn("送料無料", msg)

        ok, msg = check_shipping_trap("着払い（購入者負担）にて発送いたします。")
        self.assertFalse(ok)
        self.assertIn("着払い", msg)

    def test_iata_lithium_compliance(self):
        valid_basket = [
            {"model": "PS Vita 2000", "battery_type": "li-ion"},
            {"model": "PSP-3000", "battery_type": "li-ion"},
            {"model": "Game Boy Color", "battery_type": "none"},
            {"model": "Canon Autoboy", "battery_type": "none"}
        ]
        ok, msg = check_iata_lithium(valid_basket)
        self.assertTrue(ok)
        self.assertIn("2/2", msg)

        invalid_basket = [
            {"model": "PS Vita 2000", "battery_type": "li-ion"},
            {"model": "PSP-3000", "battery_type": "li-ion"},
            {"model": "New Nintendo 3DS XL", "battery_type": "li-ion"}
        ]
        ok, msg = check_iata_lithium(invalid_basket)
        self.assertFalse(ok)
        self.assertIn("Przekroczono limit IATA", msg)

    def test_profitability_hurdle(self):
        good_deal = {"est_margin_pln": 150.0, "roi_percent": 65.0}
        ok, msg = check_profitability_hurdle(good_deal)
        self.assertTrue(ok)

        low_margin = {"est_margin_pln": 15.0, "roi_percent": 12.0}
        ok, msg = check_profitability_hurdle(low_margin)
        self.assertFalse(ok)

    def test_currency_health(self):
        ok, _ = check_currency_health(0.0248, 4.35)
        self.assertTrue(ok)

        ok, msg = check_currency_health(0.005, 4.35)
        self.assertFalse(ok)
        self.assertIn("Anomalia kursu JPY", msg)

    def test_watchlist_camera_price_compliance(self):
        # Watchlist must not contain any camera > 100 PLN
        ok, errs = check_dataset_integrity(WATCHLIST_FILE, expected_type="watchlist")
        self.assertTrue(ok, f"Błędy w watchlist: {errs}")

    def test_yahoo_deals_camera_price_compliance(self):
        # Yahoo deals must not contain any camera > 100 PLN
        ok, errs = check_dataset_integrity(YAHOO_DEALS_FILE, expected_type="yahoo_deals")
        self.assertTrue(ok, f"Błędy w yahoo_deals: {errs}")

    def test_markdown_dashboards_exist(self):
        ok, errs = check_markdown_dashboards(BASE_DIR)
        self.assertTrue(ok, f"Błędy dashboardów: {errs}")

    def test_run_full_system_audit(self):
        audit = run_full_system_audit()
        self.assertTrue(audit["success"])
        self.assertEqual(audit["failed_checks"], 0)
        self.assertGreaterEqual(audit["total_checks"], 4)


if __name__ == "__main__":
    unittest.main()
