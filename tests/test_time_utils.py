"""Unit tests for time_utils, ensuring expired auctions never resurrect and Europe/Warsaw timezone is respected."""

import unittest
from datetime import datetime, timezone, timedelta
import zoneinfo
from watcher.time_utils import calculate_auction_timing, format_time_remaining, TZ_WARSAW, TZ_TOKYO


class TestTimeUtils(unittest.TestCase):

    def test_past_auction_is_ended_and_not_resurrected(self):
        """Regression test for F03: past end times must not be resurrected into future deadlines."""
        ref_now = datetime(2026, 11, 11, 12, 0, tzinfo=timezone.utc)
        # Auction ended yesterday
        deal = {
            "ends_at": "2026-11-10 12:00 UTC",
            "time_remaining_minutes": 60  # old stale minutes
        }
        timing = calculate_auction_timing(deal, ref_time_utc=ref_now)
        self.assertTrue(timing["is_ended"], "Auction ending yesterday must have is_ended == True")
        self.assertEqual(timing["time_remaining_minutes"], 0)
        self.assertEqual(timing["time_remaining_formatted"], "Zakończona")
        self.assertIn("2026-11-10", timing["ends_at"])
        self.assertFalse(timing["is_ending_soon"])

    def test_future_auction_calculates_exact_remaining_minutes(self):
        ref_now = datetime(2026, 11, 11, 12, 0, tzinfo=timezone.utc)
        # Auction ends in 45 minutes
        deal = {
            "ends_at": "2026-11-11 12:45 UTC"
        }
        timing = calculate_auction_timing(deal, ref_time_utc=ref_now)
        self.assertFalse(timing["is_ended"])
        self.assertEqual(timing["time_remaining_minutes"], 45)
        self.assertEqual(timing["time_remaining_formatted"], "45 min")
        self.assertTrue(timing["is_ending_soon"])

    def test_warsaw_timezone_formatting(self):
        # 12:00 UTC in November (standard CET = UTC+1) -> 13:00 Warsaw
        ref_now = datetime(2026, 11, 11, 10, 0, tzinfo=timezone.utc)
        deal = {
            "ends_at": "2026-11-11 12:00 UTC"
        }
        timing = calculate_auction_timing(deal, ref_time_utc=ref_now)
        self.assertEqual(timing["ends_at_pl"], "13:00")
        self.assertEqual(timing["ends_at_jst"], "21:00")
        self.assertIn("13:00 (PL)", timing["ends_at_formatted"])
        self.assertIn("21:00 (JP)", timing["ends_at_formatted"])

    def test_format_time_remaining(self):
        self.assertEqual(format_time_remaining(0), "Zakończona")
        self.assertEqual(format_time_remaining(-5), "Zakończona")
        self.assertEqual(format_time_remaining(15), "15 min")
        self.assertEqual(format_time_remaining(60), "1h")
        self.assertEqual(format_time_remaining(75), "1h 15m")
        self.assertEqual(format_time_remaining(1440), "1d")
        self.assertEqual(format_time_remaining(1500), "1d 1h")


if __name__ == "__main__":
    unittest.main()
