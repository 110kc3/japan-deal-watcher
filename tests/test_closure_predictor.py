import unittest

from watcher.closure_predictor import ConditionGrade, ConditionAnalyzer, AuctionClosurePredictor
from watcher.config import DEFAULT_JPY_PLN_RATE, DEFAULT_EUR_PLN_RATE, MAX_CAMERA_PRICE_PLN, MAX_LENS_PRICE_PLN

class TestClosurePredictor(unittest.TestCase):
    def test_condition_detection_mint_box(self):
        deal = {
            "model": "New Nintendo 3DS LL",
            "custom_note": "Kompletny box CIB z oryginalnym pudełkiem i instrukcjami, stan gabinetowy",
            "category_id": "nintendo_3ds_handhelds"
        }
        res = ConditionAnalyzer.detect_condition(deal)
        self.assertEqual(res["grade"], ConditionGrade.MINT_BOX)
        self.assertIn("Oryginalne pudełko (CIB)", res["features"])

    def test_condition_detection_untested_junk(self):
        deal = {
            "model": "Karton 50 Gier Retro Danshari",
            "custom_note": "Likwidacja pokoju ze strychu, pakiety hurtowe niesprawdzony",
            "category_id": "danshari_mystery_lots"
        }
        res = ConditionAnalyzer.detect_condition(deal)
        self.assertEqual(res["grade"], ConditionGrade.UNTESTED_JUNK)
        self.assertIn("Paczka hurtowa / Danshari", res["features"])

    def test_condition_detection_flawed(self):
        deal = {
            "model": "Nintendo DS Lite White",
            "custom_note": "Sprawny 100%, ale widoczne żółknięcie obudowy na zawiasie",
            "category_id": "nintendo_ds_handhelds"
        }
        res = ConditionAnalyzer.detect_condition(deal)
        self.assertEqual(res["grade"], ConditionGrade.FLAWED_WORKING)
        self.assertIn("Pożółknięcie obudowy / IPS", res["features"])

    def test_condition_detection_console_only(self):
        deal = {
            "model": "Sony PSP-3000 Piano Black",
            "custom_note": "Sama konsola bez pudełka i ładowarki, sprawna",
            "category_id": "psp_handheld"
        }
        res = ConditionAnalyzer.detect_condition(deal)
        self.assertEqual(res["grade"], ConditionGrade.GOOD_CONSOLE_ONLY)

    def test_predict_closure_calculation(self):
        deal = {
            "id": "test_deal",
            "model": "PS Vita Slim PCH-2000",
            "category_id": "ps_vita",
            "price_jpy": 8000,
            "closed_price_avg_jpy": 11500,
            "closed_price_min_jpy": 9500,
            "closed_price_max_jpy": 13500,
            "est_pl_value": 650.0,
            "time_remaining_minutes": 180,
            "custom_note": "Zadbany egzemplarz, w 100% sprawny technicznie"
        }
        pred = AuctionClosurePredictor.predict_closure(deal, DEFAULT_JPY_PLN_RATE, DEFAULT_EUR_PLN_RATE)
        self.assertEqual(pred["condition_grade"], ConditionGrade.VERY_GOOD)
        self.assertGreater(pred["predicted_closure_jpy"], deal["price_jpy"])
        self.assertGreater(pred["expected_margin_pln"], 0)
        self.assertIn("verdict_label", pred)
        self.assertIn("recommendation_text", pred)

    def test_condition_detection_empty_is_unknown(self):
        res = ConditionAnalyzer.detect_condition({})
        self.assertEqual(res["grade"], ConditionGrade.UNKNOWN)
        self.assertIn("Stan techniczny nieznany", res["features"])

    def test_camera_and_lens_strict_cap(self):
        cam_deal = {
            "id": "cam_test",
            "model": "Olympus Mju II",
            "category_id": "film_cameras_point_shoot",
            "price_jpy": 3800,
            "closed_price_avg_jpy": 9500,
            "est_pl_value": 850.0,
            "time_remaining_minutes": 14,
            "custom_note": "Aparat analogowy point & shoot"
        }
        pred = AuctionClosurePredictor.predict_closure(cam_deal, DEFAULT_JPY_PLN_RATE, DEFAULT_EUR_PLN_RATE)
        max_bid_pln = pred["max_sniper_bid_jpy"] * DEFAULT_JPY_PLN_RATE
        self.assertLessEqual(max_bid_pln, MAX_CAMERA_PRICE_PLN + 0.5)

    def test_verdict_tiers(self):
        s_deal = {
            "id": "s_deal",
            "model": "Cult Retro Bundle",
            "category_id": "retro_games_mix",
            "price_jpy": 2500,
            "closed_price_avg_jpy": 3500,
            "est_pl_value": 750.0,
            "time_remaining_minutes": 35,
            "custom_note": "Pudełkowy zestaw gier retro mix"
        }
        pred_s = AuctionClosurePredictor.predict_closure(s_deal, DEFAULT_JPY_PLN_RATE, DEFAULT_EUR_PLN_RATE)
        self.assertIn("S-TIER", pred_s["verdict_label"])

if __name__ == "__main__":
    unittest.main()
