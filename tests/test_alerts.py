"""Unit tests for Selective Discovery and Alerts Engine (Task 5)."""

import json
import tempfile
import unittest
from pathlib import Path

from watcher.alerts import AlertsEngine
from watcher.config import DEFAULT_JPY_PLN_RATE, DEFAULT_EUR_PLN_RATE

class TestAlertsEngine(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.alerts_file = Path(self.temp_dir.name) / "test_alerts_history.json"
        self.engine = AlertsEngine(
            alerts_file=self.alerts_file,
            min_roi=25.0,
            min_margin_pln=40.0,
            rate_jpy=DEFAULT_JPY_PLN_RATE,
            rate_eur=DEFAULT_EUR_PLN_RATE
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_gate_rejection_defects_and_junk(self):
        """Broken or junk items must fail the defects gate and never emit alerts."""
        broken_deal = {
            "id": "m_broken_001",
            "model": "Sony PS Vita PCH-2000 Black",
            "price_jpy": 2000,
            "est_pl_value": 450.0,
            "custom_note": "Ekran pęknięty, 液晶割れ, nie włącza się"
        }
        res = self.engine.evaluate_gates(broken_deal)
        self.assertFalse(res["eligible"])
        self.assertIn("defects_and_traps", res["failed_gates"])

        alert = self.engine.process_candidate(broken_deal)
        self.assertIsNone(alert)

    def test_gate_rejection_camera_price_cap(self):
        """Camera above 100 PLN strict cap must fail price_caps gate."""
        expensive_camera = {
            "id": "cam_over_cap_001",
            "model": "Olympus Mju-II Zoom 80",
            "category_id": "film_cameras_point_shoot",
            "price_jpy": 6000,
            "est_pl_value": 400.0
        }
        res = self.engine.evaluate_gates(expensive_camera)
        self.assertFalse(res["eligible"])
        self.assertIn("price_caps", res["failed_gates"])

        alert = self.engine.process_candidate(expensive_camera)
        self.assertIsNone(alert)

    def test_gate_rejection_empty_box_trap(self):
        """Empty box listings (箱のみ) must fail defects_and_traps gate."""
        trap_deal = {
            "id": "trap_001",
            "model": "GBA SP Onyx Black 外箱 取扱説明書 箱のみ",
            "price_jpy": 1500,
            "est_pl_value": 250.0
        }
        res = self.engine.evaluate_gates(trap_deal)
        self.assertFalse(res["eligible"])
        self.assertIn("defects_and_traps", res["failed_gates"])

    def test_gate_rejection_low_margin(self):
        """Items with insufficient profit margin must fail profitability gate."""
        low_margin_deal = {
            "id": "low_margin_001",
            "model": "Generic Game Boy Cartridge",
            "category_id": "retro_games_mix",
            "price_jpy": 2500,
            "est_pl_value": 120.0
        }
        res = self.engine.evaluate_gates(low_margin_deal)
        self.assertFalse(res["eligible"])
        self.assertIn("profitability", res["failed_gates"])

    def test_gate_rejection_battery_limit_excess(self):
        """Single item with 4 consoles and lithium batteries exceeds 2-battery parcel limit."""
        excess_battery_deal = {
            "id": "psp_lot_4",
            "model": "Sony PSP 4台 大量セット",
            "category_id": "psp_handheld",
            "price_jpy": 5000,
            "est_pl_value": 600.0
        }
        res = self.engine.evaluate_gates(excess_battery_deal)
        self.assertFalse(res["eligible"])
        self.assertIn("logistics", res["failed_gates"])

    def test_emit_new_opportunity_alert(self):
        """Qualified deal meeting all gates emits a new_opportunity alert and persists it."""
        deal = {
            "id": "m_gem_001",
            "model": "Nintendo DS Lite Polar White",
            "category_id": "nintendo_ds_handhelds",
            "price_jpy": 2500,
            "est_pl_value": 240.0,
            "condition": "Bardzo dobry stan, 動作確認済",
            "shipping_share_pln": 30.0
        }
        gate_res = self.engine.evaluate_gates(deal)
        self.assertTrue(gate_res["eligible"])

        alert = self.engine.process_candidate(deal)
        self.assertIsNotNone(alert)
        self.assertEqual(alert["alert_type"], "new_opportunity")
        self.assertEqual(alert["listing_id"], "m_gem_001")
        self.assertEqual(alert["confidence"], "high")
        self.assertGreater(alert["net_margin_pln"], 40.0)
        self.assertGreater(alert["roi_pct"], 25.0)

        self.assertTrue(self.alerts_file.exists())
        with open(self.alerts_file, "r", encoding="utf-8") as f:
            saved = json.load(f)
            self.assertEqual(saved["total_alerts"], 1)
            self.assertEqual(saved["alerts"][0]["listing_id"], "m_gem_001")

    def test_alert_deduplication(self):
        """Scanning the same deal twice at the same price must not emit duplicate alerts."""
        deal = {
            "id": "m_gem_002",
            "model": "Game Boy Advance SP Silver",
            "category_id": "gameboy_advance_retro",
            "price_jpy": 3000,
            "est_pl_value": 280.0
        }
        alert1 = self.engine.process_candidate(deal)
        self.assertIsNotNone(alert1)

        alert2 = self.engine.process_candidate(deal)
        self.assertIsNone(alert2)

        alerts = self.engine.get_alerts()
        self.assertEqual(len(alerts), 1)

    def test_emit_price_drop_alert(self):
        """When an alerted or tracked deal drops in price, emit a price_drop alert."""
        deal = {
            "id": "m_drop_001",
            "model": "Sony PS Vita Aqua Blue",
            "category_id": "ps_vita",
            "price_jpy": 8000,
            "est_pl_value": 550.0
        }
        alert1 = self.engine.process_candidate(deal)
        self.assertIsNotNone(alert1)
        self.assertEqual(alert1["alert_type"], "new_opportunity")

        deal_dropped = dict(deal)
        deal_dropped["price_jpy"] = 6000

        alert2 = self.engine.process_candidate(deal_dropped)
        self.assertIsNotNone(alert2)
        self.assertEqual(alert2["alert_type"], "price_drop")
        self.assertEqual(alert2["price_drop_jpy"], 2000.0)
        self.assertEqual(alert2["current_price_jpy"], 6000.0)
        self.assertIn("SPADEK CENY", alert2["summary"])

        alerts = self.engine.get_alerts()
        self.assertEqual(len(alerts), 2)
        self.assertEqual(alerts[0]["alert_type"], "price_drop")

    def test_batch_processing_and_clear_history(self):
        """Tests processing multiple items in batch and clearing history."""
        deals = [
            {
                "id": "d1",
                "model": "Nintendo DS Lite Blue",
                "category_id": "nintendo_ds_handhelds",
                "price_jpy": 2200,
                "est_pl_value": 210.0
            },
            {
                "id": "d2",
                "model": "Broken Game Boy",
                "price_jpy": 1000,
                "custom_note": "ジャンク 起動不可",
                "est_pl_value": 200.0
            },
            {
                "id": "d3",
                "model": "PS Vita OLED Black",
                "category_id": "ps_vita",
                "price_jpy": 7500,
                "est_pl_value": 520.0
            }
        ]
        emitted = self.engine.process_batch(deals)
        self.assertEqual(len(emitted), 2)

        alerted_ids = self.engine.get_alerted_ids()
        self.assertIn("d1", alerted_ids)
        self.assertIn("d3", alerted_ids)
        self.assertNotIn("d2", alerted_ids)

        self.engine.clear_history()
        self.assertEqual(len(self.engine.get_alerts()), 0)
        self.assertEqual(len(self.engine.get_alerted_ids()), 0)

if __name__ == "__main__":
    unittest.main()
