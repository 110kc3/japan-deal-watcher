import unittest
from datetime import date, timedelta
from watcher.consolidation import (
    ConsolidationTracker,
    resolve_item_weight,
    calculate_package_weight,
    estimate_shipping_cost_by_method,
    calculate_shipping_rates_by_weight,
    calculate_residual_profit
)
from watcher.config import DEFAULT_JPY_PLN_RATE, DEFAULT_EUR_PLN_RATE

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

    def test_package_weight_and_shipping_methods(self):
        items = [
            {"category_id": "nintendo_3ds_handhelds", "model": "New 3DS LL"},
            {"category_id": "ps_vita", "model": "PS Vita 2000"},
            {"category_id": "gameboy_advance_retro", "model": "GBA SP"}
        ]
        # Weights: 320 + 290 + 200 = 810g. Box buffer = 300g. Total = 1110g.
        pw = calculate_package_weight(items)
        self.assertEqual(pw["net_weight_g"], 810)
        self.assertEqual(pw["box_buffer_g"], 300)
        self.assertEqual(pw["total_weight_g"], 1110)
        self.assertEqual(pw["total_weight_kg"], 1.11)
        self.assertTrue(pw["is_avia_eligible"])
        self.assertEqual(pw["avia_remaining_g"], 890)
        self.assertEqual(pw["avia_overweight_g"], 0)

        # Shipping rates for 1,110g
        rates = calculate_shipping_rates_by_weight(pw["total_weight_g"], rate_jpy=DEFAULT_JPY_PLN_RATE)
        self.assertEqual(rates["recommended_method_id"], "avia_small_packet")
        self.assertTrue(rates["methods"]["avia_small_packet"]["is_available"])
        self.assertGreater(rates["methods"]["avia_small_packet"]["cost_pln"], 0)

    def test_package_over_avia_limit(self):
        items = [
            {"category_id": "danshari_mystery_lots", "model": "Mystery Box 1"},
            {"category_id": "high_margin_curated_consoles", "model": "PS4 Pro Rathalos"}
        ]
        # Weights: 1800 + 2500 = 4300g. Box buffer = 300g. Total = 4600g.
        pw = calculate_package_weight(items)
        self.assertEqual(pw["total_weight_g"], 4600)
        self.assertFalse(pw["is_avia_eligible"])
        self.assertEqual(pw["avia_remaining_g"], 0)
        self.assertEqual(pw["avia_overweight_g"], 2600)

        rates = calculate_shipping_rates_by_weight(pw["total_weight_g"], rate_jpy=DEFAULT_JPY_PLN_RATE)
        self.assertFalse(rates["methods"]["avia_small_packet"]["is_available"])
        self.assertTrue(rates["methods"]["ems_express"]["is_available"])
        self.assertTrue(rates["methods"]["surface_sea"]["is_available"])

    def test_calculate_residual_profit(self):
        items = [
            {
                "id": "item1",
                "model": "Nintendo 3DS",
                "category_id": "nintendo_3ds_handhelds",
                "price_jpy": 8000,
                "est_pl_value": 650.0,
                "has_battery": True
            },
            {
                "id": "item2",
                "model": "GBA SP",
                "category_id": "gameboy_advance_retro",
                "price_jpy": 4000,
                "est_pl_value": 450.0,
                "has_battery": True
            }
        ]
        res = calculate_residual_profit(items, rate_jpy=DEFAULT_JPY_PLN_RATE, rate_eur=DEFAULT_EUR_PLN_RATE)
        self.assertEqual(res["total_items"], 2)
        self.assertEqual(res["total_resale_pln"], 1100.0)
        self.assertEqual(res["total_purchase_jpy"], 12000)
        self.assertGreater(res["shipping_cost_pln"], 0)
        self.assertGreater(res["total_landed_cost_pln"], 0)
        self.assertGreater(res["residual_profit_pln"], 0)
        # Residual profit + landed cost must equal total resale
        self.assertAlmostEqual(res["residual_profit_pln"] + res["total_landed_cost_pln"], res["total_resale_pln"], delta=0.05)

if __name__ == "__main__":
    unittest.main()
