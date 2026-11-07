import unittest
from watcher.markdown_generator import MarkdownGenerator, sanitize_md

class TestMarkdownGenerator(unittest.TestCase):
    def test_sanitize_md(self):
        self.assertEqual(sanitize_md("Item | with | pipe"), "Item &#124; with &#124; pipe")
        self.assertEqual(sanitize_md("Item with\nnewline\r"), "Item with newline")
        self.assertEqual(sanitize_md(None), "")
        self.assertEqual(sanitize_md("Clean Text"), "Clean Text")

    def test_format_margin(self):
        # Positive margin
        pos = MarkdownGenerator.format_margin(120.5, 45.2)
        self.assertIn("+120.50 zł", pos)
        self.assertIn("+45.2%", pos)
        self.assertIn("#10b981", pos)

        # Negative margin
        neg = MarkdownGenerator.format_margin(-25.0, -8.5)
        self.assertIn("-25.00 zł", neg)
        self.assertNotIn("+-", neg)  # Ensure no double +- bug
        self.assertIn("#ef4444", neg)

        # Zero margin
        zero = MarkdownGenerator.format_margin(0.0, 0.0)
        self.assertIn("0.00 zł", zero)

    def test_generate_structure(self):
        timeline = {
            "start_date": "2026-11-07",
            "deadline": "2027-01-06",
            "days_passed": 0,
            "days_remaining": 60,
            "status_badge": "🟢 Safe",
            "status_color": "brightgreen"
        }
        deals = [
            {
                "id": "m111",
                "model": "PS Vita Slim",
                "color": "Neon Orange",
                "custom_note": "Great condition",
                "category_name": "PlayStation Vita",
                "battery_type": "li-ion",
                "price_jpy": 13000,
                "price_pln_raw": 322.8,
                "landed_cost_pln": 460.0,
                "est_pl_value": 900.0,
                "est_margin_pln": 440.0,
                "roi_percent": 95.6,
                "status": "Dostępne",
                "mercari_url": "https://jp.mercari.com/item/m111",
                "zenmarket_url": "https://zenmarket.jp/pl/mercariproduct.aspx?itemCode=m111"
            }
        ]

        gen = MarkdownGenerator(deals=deals, timeline_status=timeline, rate=0.024832, is_live_rate=True)
        md = gen.generate()

        self.assertIn("# 🇯🇵 Japan Deal Watcher", md)
        self.assertIn("NBP%20Live", md)
        self.assertIn("60-Day Warehouse Packing & Consolidation Timeline", md)
        self.assertIn("Top 3 Snipes", md)
        self.assertIn("PS Vita Slim", md)
        self.assertIn("+440.00 zł", md)
        self.assertIn("ZenMarket 1-Click", md)

if __name__ == "__main__":
    unittest.main()
