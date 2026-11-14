"""Unit tests for ResaleLedger and owner resale learning engine.

Verifies:
- State transitions: planned -> bought -> in_warehouse -> shipped -> received_tested -> listed -> sold / returned.
- Core rule: NO realized profit before confirmed settlement (status == 'sold').
- Financial calculations: landed cost, net settlement, realized profit, realized ROI.
- Returns and refund adjustments.
- Metric calculations: capital tied up (capital at risk), realized profit, win rate, average days to cash.
- CSV and JSON private export/backup.
- Safe storage: atomic writes and corruption quarantining.
"""

import csv
import json
import tempfile
import unittest
from pathlib import Path

from watcher.resale_ledger import ResaleLedger, LIFECYCLE_STAGES, CSV_FIELDNAMES
from watcher.storage import atomic_write_json, read_json_safe

class TestResaleLedger(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.ledger_file = Path(self.temp_dir.name) / "test_resale_ledger.json"
        self.ledger = ResaleLedger(filepath=self.ledger_file)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_initialization_creates_empty_ledger(self):
        """Ledger initializes cleanly with proper metadata structure."""
        self.assertEqual(len(self.ledger.data["items"]), 0)
        self.assertEqual(self.ledger.data["metadata"]["total_items"], 0)

    def test_add_item_defaults_to_planned(self):
        """Adding item defaults to planned stage and computes landed cost."""
        item_data = {
            "item_id": "item_001",
            "model": "Nintendo New 3DS XL Metallic Blue",
            "category_id": "nintendo_3ds_handhelds",
            "purchase_price_jpy": 10000,
            "fx_rate_jpy_pln": 0.025,
            "actual_fees_pln": 28.0,
            "actual_freight_pln": 30.0,
            "actual_customs_vat_pln": 70.84,
            "testing_repair_cost_pln": 15.0,
            "handling_hours": 1.5,
            "notes": "Mint condition in original box"
        }
        item = self.ledger.add_item(item_data)

        self.assertEqual(item["item_id"], "item_001")
        self.assertEqual(item["status"], "planned")
        self.assertAlmostEqual(item["landed_cost_pln"], 378.84, places=2)
        self.assertIsNone(item["realized_profit_pln"])
        self.assertIsNone(item["realized_roi_pct"])

    def test_lifecycle_stage_transitions(self):
        """Verifies orderly stage progression: planned -> bought -> in_warehouse -> shipped -> received_tested -> listed -> sold."""
        item = self.ledger.add_item({"item_id": "ds_lite_01", "model": "Nintendo DS Lite"})
        self.assertEqual(item["status"], "planned")

        self.ledger.transition_status("ds_lite_01", "bought", notes="Won Yahoo auction")
        self.assertEqual(self.ledger.get_item("ds_lite_01")["status"], "bought")

        self.ledger.transition_status("ds_lite_01", "in_warehouse", notes="Arrived in Osaka warehouse")
        self.assertEqual(self.ledger.get_item("ds_lite_01")["status"], "in_warehouse")

        self.ledger.transition_status("ds_lite_01", "shipped", notes="Dispatched via AVIA parcel")
        self.assertEqual(self.ledger.get_item("ds_lite_01")["status"], "shipped")

        self.ledger.transition_status("ds_lite_01", "received_tested", notes="Received in Poland, fully working")
        self.assertEqual(self.ledger.get_item("ds_lite_01")["status"], "received_tested")

        self.ledger.transition_status("ds_lite_01", "listed", listing_channel="Allegro")
        self.assertEqual(self.ledger.get_item("ds_lite_01")["status"], "listed")

        with self.assertRaises(ValueError):
            self.ledger.transition_status("ds_lite_01", "in_warehouse", force=False)

    def test_record_settlement_locks_realized_profit(self):
        """Settlement calculates net payout and locks in realized profit and ROI."""
        self.ledger.add_item({
            "item_id": "vita_001",
            "model": "PS Vita Aqua Blue",
            "category_id": "ps_vita",
            "purchase_date": "2026-11-01",
            "purchase_price_jpy": 12000,
            "fx_rate_jpy_pln": 0.025,
            "actual_fees_pln": 28.0,
            "actual_freight_pln": 30.0,
            "actual_customs_vat_pln": 82.34,
            "landed_cost_pln": 440.34,
            "testing_repair_cost_pln": 10.0,
            "handling_hours": 2.0,
            "status": "listed"
        })

        res = self.ledger.record_settlement(
            item_id="vita_001",
            sale_price_pln=750.0,
            selling_fees_pln=65.0,
            shipping_packing_cost_pln=15.0,
            sale_date="2026-11-15",
            settlement_date="2026-11-16",
            listing_channel="Allegro"
        )

        self.assertEqual(res["status"], "sold")
        self.assertEqual(res["net_settlement_pln"], 670.0)
        self.assertAlmostEqual(res["realized_profit_pln"], 219.66, places=2)
        self.assertAlmostEqual(res["realized_roi_pct"], 48.78, places=1)
        self.assertEqual(res["listing_channel"], "Allegro")

    def test_core_rule_no_realized_profit_before_sold_settlement(self):
        """CORE RULE: No realized profit is credited to listed or planned inventory."""
        self.ledger.add_item({
            "item_id": "lens_01",
            "model": "Super Takumar 50mm f/1.4",
            "landed_cost_pln": 180.0,
            "sale_price_pln": 350.0,
            "status": "listed"
        })
        item = self.ledger.get_item("lens_01")
        self.assertIsNone(item["realized_profit_pln"])
        self.assertIsNone(item["realized_roi_pct"])

        metrics = self.ledger.get_metrics()
        self.assertEqual(metrics["total_realized_profit_pln"], 0.0)
        self.assertEqual(metrics["capital_at_risk_pln"], 180.0)

    def test_refund_and_returns(self):
        """Buyer returns item: transitions to 'returned', clears realized profit, item remains capital at risk."""
        self.ledger.add_item({
            "item_id": "cam_01",
            "model": "Canon Autoboy Luna",
            "landed_cost_pln": 150.0,
            "testing_repair_cost_pln": 0.0,
            "status": "listed"
        })

        self.ledger.record_settlement(
            item_id="cam_01",
            sale_price_pln=300.0,
            selling_fees_pln=25.0,
            shipping_packing_cost_pln=15.0
        )
        item = self.ledger.get_item("cam_01")
        self.assertEqual(item["status"], "sold")
        self.assertGreater(item["realized_profit_pln"], 0)

        self.ledger.record_refund(
            item_id="cam_01",
            refund_amount_pln=300.0,
            mark_returned=True,
            notes="Buyer returned due to shutter issue"
        )
        returned_item = self.ledger.get_item("cam_01")
        self.assertEqual(returned_item["status"], "returned")
        self.assertEqual(returned_item["refund_amount_pln"], 300.0)
        self.assertIsNone(returned_item["realized_profit_pln"])

        metrics = self.ledger.get_metrics()
        self.assertEqual(metrics["total_realized_profit_pln"], 0.0)
        self.assertEqual(metrics["capital_at_risk_pln"], 150.0)

    def test_partial_refund_without_return_adjusts_profit(self):
        """Partial discount granted to buyer without return adjusts realized profit."""
        self.ledger.add_item({
            "item_id": "psp_01",
            "model": "PSP-3000 Pink",
            "landed_cost_pln": 200.0,
            "status": "listed"
        })
        self.ledger.record_settlement(
            item_id="psp_01",
            sale_price_pln=400.0,
            selling_fees_pln=30.0,
            shipping_packing_cost_pln=10.0
        )
        self.assertEqual(self.ledger.get_item("psp_01")["realized_profit_pln"], 160.0)

        self.ledger.record_refund(
            item_id="psp_01",
            refund_amount_pln=40.0,
            mark_returned=False,
            notes="Partial refund for scratch"
        )
        item = self.ledger.get_item("psp_01")
        self.assertEqual(item["status"], "sold")
        self.assertEqual(item["realized_profit_pln"], 120.0)

    def test_metrics_capital_at_risk_win_rate_days_to_cash(self):
        """Computes comprehensive executive metrics."""
        self.ledger.add_item({
            "item_id": "active_01",
            "model": "Game Boy Micro",
            "purchase_date": "2026-11-01",
            "landed_cost_pln": 300.0,
            "testing_repair_cost_pln": 20.0,
            "status": "listed"
        })

        self.ledger.add_item({
            "item_id": "sold_win",
            "model": "DS Lite Black",
            "purchase_date": "2026-11-01",
            "landed_cost_pln": 100.0,
            "testing_repair_cost_pln": 0.0,
            "status": "listed"
        })
        self.ledger.record_settlement(
            item_id="sold_win",
            sale_price_pln=270.0,
            selling_fees_pln=20.0,
            shipping_packing_cost_pln=0.0,
            sale_date="2026-11-11",
            settlement_date="2026-11-11",
            listing_channel="Allegro"
        )

        self.ledger.add_item({
            "item_id": "sold_loss",
            "model": "Broken GBA SP",
            "purchase_date": "2026-11-01",
            "landed_cost_pln": 100.0,
            "testing_repair_cost_pln": 0.0,
            "status": "listed"
        })
        self.ledger.record_settlement(
            item_id="sold_loss",
            sale_price_pln=90.0,
            selling_fees_pln=10.0,
            shipping_packing_cost_pln=0.0,
            sale_date="2026-11-21",
            settlement_date="2026-11-21",
            listing_channel="OLX"
        )

        metrics = self.ledger.get_metrics()
        self.assertEqual(metrics["total_items"], 3)
        self.assertEqual(metrics["capital_at_risk_pln"], 320.0)
        self.assertEqual(metrics["total_sales_count"], 2)
        self.assertEqual(metrics["profitable_sales_count"], 1)
        self.assertEqual(metrics["unprofitable_sales_count"], 1)
        self.assertEqual(metrics["win_rate_pct"], 50.0)
        self.assertAlmostEqual(metrics["total_realized_profit_pln"], 130.0, places=2)
        self.assertEqual(metrics["avg_days_to_cash"], 15.0)

        self.assertIn("Allegro", metrics["by_channel"])
        self.assertIn("OLX", metrics["by_channel"])
        self.assertEqual(metrics["by_channel"]["Allegro"]["sales_count"], 1)
        self.assertEqual(metrics["by_channel"]["OLX"]["sales_count"], 1)

    def test_export_csv(self):
        """Exports ledger to standard CSV with all 22 required columns."""
        self.ledger.add_item({
            "item_id": "csv_test_01",
            "model": "PSP-2000 Silver",
            "purchase_price_jpy": 5000,
            "status": "bought"
        })
        csv_path = Path(self.temp_dir.name) / "resale_export.csv"
        out_path = self.ledger.export_csv(filepath=csv_path)

        self.assertTrue(out_path.exists())
        with open(out_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["item_id"], "csv_test_01")
        self.assertEqual(rows[0]["model"], "PSP-2000 Silver")
        for col in CSV_FIELDNAMES:
            self.assertIn(col, rows[0])

    def test_export_json_and_atomic_persistence(self):
        """Exports private backup JSON including metrics and items."""
        self.ledger.add_item({
            "item_id": "json_test_01",
            "model": "DualSense 30th",
            "status": "planned"
        })
        json_backup_path = Path(self.temp_dir.name) / "resale_backup.json"
        out_path = self.ledger.export_json(filepath=json_backup_path)

        self.assertTrue(out_path.exists())
        with open(out_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIn("metadata", data)
        self.assertIn("metrics", data)
        self.assertIn("items", data)
        self.assertIn("json_test_01", data["items"])

    def test_safe_storage_quarantine_corrupt_file(self):
        """If a corrupted file exists on load, it is quarantined and not silently wiped."""
        corrupt_file = Path(self.temp_dir.name) / "corrupt_ledger.json"
        with open(corrupt_file, "w", encoding="utf-8") as f:
            f.write("{this is not valid json!@@#$")

        new_ledger = ResaleLedger(filepath=corrupt_file)
        self.assertEqual(len(new_ledger.data["items"]), 0)

        corrupt_copies = list(Path(self.temp_dir.name).glob("corrupt_ledger.json.corrupt.*"))
        self.assertEqual(len(corrupt_copies), 1)
        with open(corrupt_copies[0], "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, "{this is not valid json!@@#$")

if __name__ == "__main__":
    unittest.main()
