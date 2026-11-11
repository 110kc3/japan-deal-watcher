import unittest
from datetime import date, timedelta
from watcher.consolidation import (
    ConsolidationTracker,
    resolve_item_weight,
    calculate_package_weight,
    estimate_shipping_cost_by_method,
    calculate_shipping_rates_by_weight,
    calculate_residual_profit,
    calculate_marginal_freight,
    resolve_item_battery_count,
    apply_battery_disposal
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

    def test_marginal_freight_within_avia_limit(self):
        """Adding a lightweight item within 2,000g AVIA limit incurs only small marginal freight."""
        current_items = [
            {"model": "Nintendo DS Lite", "category_id": "nintendo_ds_handhelds", "price_jpy": 3000, "est_pl_value": 180.0}
        ]
        # DS Lite is ~280g + 300g box buffer = 580g (AVIA)
        candidate = {
            "model": "Game Boy Advance SP",
            "category_id": "gameboy_advance_retro",
            "price_jpy": 2500,
            "est_pl_value": 220.0
        }
        res = calculate_marginal_freight(current_items, candidate)
        self.assertFalse(res["crossed_avia_bracket"])
        self.assertFalse(res["erases_margin"])
        self.assertGreater(res["marginal_freight_pln"], 0)
        self.assertEqual(res["recommendation"], "add_to_parcel")
        self.assertIn("Opłacalne", res["verdict"])

    def test_marginal_freight_crossing_avia_bracket_to_ems(self):
        """Crossing 2,000g AVIA ceiling into EMS significantly spikes marginal freight and flags bracket crossing."""
        # Current parcel with non-battery items totaling ~1,500g net + 300g box buffer = 1,800g (just below 2,000g AVIA limit)
        current_items = [
            {"model": "Mechanical Keyboard", "category_id": "mechanical_keyboards", "battery_type": "none"},  # 1150g
            {"model": "Retro Games Mix", "category_id": "retro_games_mix", "battery_type": "none"}            # 350g
        ]
        # Total net = 1500g + 300g buffer = 1800g (AVIA eligible)
        candidate = {
            "model": "Sony PS1 Console",
            "category_id": "ps1_consoles",  # 950g -> total becomes 2,750g (>2,000g)
            "battery_type": "none",
            "price_jpy": 2000,
            "est_pl_value": 250.0
        }
        res = calculate_marginal_freight(current_items, candidate)
        self.assertTrue(res["crossed_avia_bracket"])
        self.assertGreater(res["marginal_freight_pln"], 40.0)  # Major jump from Avia to EMS
        self.assertIn("AVIA", res["verdict"])
        self.assertEqual(res["recommendation"], "caution_bracket_crossed")

    def test_marginal_freight_erases_item_margin(self):
        """When an added item pushes freight into an expensive tier and its own margin is wiped out, reject it."""
        # Existing parcel near ceiling
        current_items = [
            {"model": "Mechanical Keyboard", "category_id": "mechanical_keyboards", "battery_type": "none"},  # 1150g
            {"model": "Analog Prime Lens", "category_id": "analog_lenses", "battery_type": "none"}            # 280g
        ]
        # Total = 1430g + 300g buffer = 1730g
        # Candidate has low resale value and high weight (pushes parcel to 3530g and expensive EMS)
        candidate = {
            "model": "Heavy mystery accessories junk",
            "category_id": "danshari_mystery_lots",  # 1800g
            "battery_type": "none",
            "price_jpy": 3000,
            "est_pl_value": 110.0  # low resale value in PL
        }
        res = calculate_marginal_freight(current_items, candidate)
        self.assertTrue(res["erases_margin"])
        self.assertEqual(res["recommendation"], "reject_marginal_freight")
        self.assertIn("kasuje zysk", res["verdict"])

    def test_multi_device_battery_tracking_and_sea_mail_rules(self):
        """Verifies multi-device bundles (e.g. 3 PSPs) accurately count 3 batteries and flags dangerous goods."""
        bundle_item = {
            "model": "【まとめ売り 3台】Sony PSP-1000 / 2000 / 3000 Pakiet Hurtowy (3 Konsole)",
            "battery_type": "li-ion"
        }
        # Multi-device bundle contains 3 internal batteries
        count = resolve_item_battery_count(bundle_item)
        self.assertEqual(count, 3)

        audit = ConsolidationTracker.audit_battery_slots([bundle_item])
        self.assertEqual(audit["li_ion_count"], 3)
        self.assertFalse(audit["is_compliant"])
        self.assertEqual(audit["excess_batteries"], 1)
        self.assertTrue(audit["sea_mail_dangerous_goods_applies"])
        self.assertIn("Japan Post", audit["sea_mail_note"])

    def test_zenmarket_battery_disposal_dry_shipping(self):
        """ZenMarket battery disposal service (300 JPY/battery) converts console to 0% Li-Ion dry ship."""
        bundle_item = {
            "id": "psp_lot_3",
            "model": "Sony PSP 3台",
            "battery_type": "li-ion",
            "battery_count": 3
        }
        disposal_result = apply_battery_disposal(bundle_item, count_to_dispose=3, rate_jpy=DEFAULT_JPY_PLN_RATE)
        self.assertEqual(disposal_result["disposed_batteries"], 3)
        self.assertEqual(disposal_result["remaining_batteries"], 0)
        self.assertEqual(disposal_result["disposal_fee_jpy"], 900)  # 3 * 300 JPY
        self.assertTrue(disposal_result["is_dry_ship"])

        # Disposed item now has 0 batteries
        dry_item = disposal_result["item"]
        self.assertEqual(resolve_item_battery_count(dry_item), 0)

        # Audit with dry item is compliant
        audit = ConsolidationTracker.audit_battery_slots([dry_item])
        self.assertEqual(audit["li_ion_count"], 0)
        self.assertTrue(audit["is_compliant"])

    def test_per_item_warehouse_storage_deadlines(self):
        """Warehouse 60-day storage limit starts on each item's arrival date, not a global single date."""
        today = date(2026, 11, 20)
        items = [
            {
                "id": "item_early",
                "model": "Nintendo DS Lite",
                "arrival_date": "2026-10-01"  # Arrived 50 days ago -> 10 days remaining
            },
            {
                "id": "item_fresh",
                "model": "PS Vita 2000",
                "arrival_date": "2026-11-15"  # Arrived 5 days ago -> 55 days remaining
            }
        ]
        tracker = ConsolidationTracker()
        status = tracker.get_timeline_status(now=today, items=items)

        self.assertEqual(status["start_date"], "2026-10-01")
        self.assertEqual(status["deadline"], "2026-11-30")  # 2026-10-01 + 60 days
        self.assertEqual(status["days_remaining"], 10)  # Governed by nearest deadline!
        self.assertIn("10 dni do opłat", status["status_badge"])

        # Check per-item breakdown
        details = status["per_item_details"]
        self.assertEqual(len(details), 2)
        early_it = next(d for d in details if d["item_id"] == "item_early")
        fresh_it = next(d for d in details if d["item_id"] == "item_fresh")

        self.assertEqual(early_it["days_remaining"], 10)
        self.assertEqual(fresh_it["days_remaining"], 55)

if __name__ == "__main__":
    unittest.main()
