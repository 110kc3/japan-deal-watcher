import unittest
from datetime import date, timedelta
from watcher.consolidation import ConsolidationTracker

class TestConsolidation(unittest.TestCase):
    def test_timeline_status_safe(self):
        start = date(2026, 11, 1)
        now = date(2026, 11, 10)
        tracker = ConsolidationTracker(start_date=start, storage_limit_days=60)
        status = tracker.get_timeline_status(now=now)

        self.assertEqual(status["start_date"], "2026-11-01")
        self.assertEqual(status["deadline"], "2026-12-31")
        self.assertEqual(status["days_passed"], 9)
        self.assertEqual(status["days_remaining"], 51)
        self.assertIn("Safe", status["status_badge"])
        self.assertEqual(status["status_color"], "brightgreen")

    def test_timeline_status_urgent_and_critical(self):
        start = date(2026, 11, 1)
        # 57 days passed -> 3 days remaining -> Critical
        now = date(2026, 11, 1) + timedelta(days=57)
        tracker = ConsolidationTracker(start_date=start, storage_limit_days=60)
        status = tracker.get_timeline_status(now=now)

        self.assertEqual(status["days_remaining"], 3)
        self.assertIn("Critical", status["status_badge"])
        self.assertEqual(status["status_color"], "red")

    def test_start_date_formats(self):
        tracker_str = ConsolidationTracker(start_date="2026-11-07")
        self.assertEqual(tracker_str.start_date, date(2026, 11, 7))

        tracker_default = ConsolidationTracker()
        self.assertEqual(tracker_default.start_date, date(2026, 11, 7))

    def test_audit_battery_slots_compliant(self):
        items = [
            {"name": "PS Vita", "battery_type": "li-ion"},
            {"name": "PSP-3000", "battery_type": "li-ion"},
            {"name": "UMD Bundle", "battery_type": "none"},
            {"name": "WonderSwan", "battery_type": "dry-cell"}
        ]
        audit = ConsolidationTracker.audit_battery_slots(items)
        self.assertEqual(audit["li_ion_count"], 2)
        self.assertEqual(audit["slots_available"], 0)
        self.assertTrue(audit["is_compliant"])
        self.assertIsNone(audit["warning"])

    def test_audit_battery_slots_exceeded(self):
        items = [
            {"name": "PS Vita 1", "battery_type": "li-ion"},
            {"name": "PS Vita 2", "battery_type": "li-ion"},
            {"name": "PSP-3000", "battery_type": "li-ion"}
        ]
        audit = ConsolidationTracker.audit_battery_slots(items)
        self.assertEqual(audit["li_ion_count"], 3)
        self.assertFalse(audit["is_compliant"])
        self.assertIn("EXCEEDED: 3/2 Li-Ion devices", audit["warning"])

    def test_calculate_parcel_savings(self):
        items = [{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}]
        savings = ConsolidationTracker.calculate_parcel_savings(items)
        self.assertEqual(savings["individual_cost_pln"], 440)
        self.assertEqual(savings["consolidated_cost_pln"], 140 + 3 * 18)
        self.assertGreater(savings["savings_pln"], 200)

        # Empty items
        empty_savings = ConsolidationTracker.calculate_parcel_savings([])
        self.assertEqual(empty_savings["savings_pln"], 0)

if __name__ == "__main__":
    unittest.main()
