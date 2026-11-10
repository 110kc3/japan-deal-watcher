"""Unit tests for FinishedAuctionsTracker."""

import unittest
import tempfile
import json
from pathlib import Path

from watcher.finished_auctions_tracker import FinishedAuctionsTracker, HISTORICAL_SEED_AUCTIONS
from watcher.config import MAX_CAMERA_PRICE_PLN, MAX_LENS_PRICE_PLN


class TestFinishedAuctionsTracker(unittest.TestCase):
    """Test suite for FinishedAuctionsTracker."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_file = Path(self.temp_dir.name) / "test_finished_auctions.json"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_initialization_with_seed_data(self):
        """Tracker initializes with historical seed data if file is absent."""
        tracker = FinishedAuctionsTracker(filepath=self.test_file)
        auctions = tracker.get_all()
        self.assertGreaterEqual(len(auctions), len(HISTORICAL_SEED_AUCTIONS))
        self.assertTrue(self.test_file.exists())

    def test_record_new_finished_auction(self):
        """Records a new finished auction and computes margin and ROI."""
        tracker = FinishedAuctionsTracker(filepath=self.test_file)
        sample = {
            "id": "t1234567890",
            "auction_id": "t1234567890",
            "model": "Nintendo New 3DS XL Metallic Blue",
            "color": "Metallic Blue",
            "category_id": "nintendo_3ds_handhelds",
            "category_name": "Nintendo 3DS",
            "price_jpy": 12000,
            "est_pl_value": 750.0,
            "battery_type": "li-ion",
            "condition_grade": "A_MINT_BOX"
        }
        rec = tracker.record_auction(sample)
        self.assertEqual(rec["auction_id"], "t1234567890")
        self.assertIn("realized_margin_pln", rec)
        self.assertGreater(rec["realized_margin_pln"], 0)
        self.assertIn("landed_cost_pln", rec)

        all_items = tracker.get_all()
        found = [x for x in all_items if x.get("id") == "t1234567890"]
        self.assertEqual(len(found), 1)

    def test_camera_price_cap_compliance(self):
        """Verifies that seed cameras and lenses strictly obey the <= 100 PLN rule."""
        tracker = FinishedAuctionsTracker(filepath=self.test_file)
        auctions = tracker.get_all()
        for a in auctions:
            cat = a.get("category_id", "")
            if cat == "film_cameras_point_shoot":
                self.assertLessEqual(
                    a.get("final_price_pln", 0),
                    MAX_CAMERA_PRICE_PLN,
                    f"Aparat {a.get('model')} przekracza 100 zł!"
                )
            if cat == "analog_lenses":
                self.assertLessEqual(
                    a.get("final_price_pln", 0),
                    MAX_LENS_PRICE_PLN,
                    f"Obiektyw {a.get('model')} przekracza 100 zł!"
                )

    def test_harvest_from_active(self):
        """Harvests expired auctions from an active list."""
        tracker = FinishedAuctionsTracker(filepath=self.test_file)
        active = [
            {
                "id": "act001",
                "auction_id": "act001",
                "model": "Sony PSP-2000 Mint",
                "time_remaining_minutes": 0,
                "is_ended": True,
                "price_jpy": 5000,
                "est_pl_value": 350.0
            },
            {
                "id": "act002",
                "auction_id": "act002",
                "model": "Sony PSP-3000 Active",
                "time_remaining_minutes": 180,
                "is_ended": False,
                "price_jpy": 6000,
                "est_pl_value": 400.0
            }
        ]
        harvested = tracker.harvest_from_active(active)
        self.assertEqual(len(harvested), 1)
        self.assertEqual(harvested[0]["id"], "act001")


if __name__ == "__main__":
    unittest.main()
