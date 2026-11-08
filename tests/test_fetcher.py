import unittest
from unittest.mock import patch, MagicMock
from watcher.fetcher import DealFetcher, classify_condition

class TestFetcher(unittest.TestCase):
    def setUp(self):
        self.fetcher = DealFetcher(rate=0.025, enable_mercapi=False)

    def test_classify_condition_broken(self):
        broken_text = "本体は電源は入りますがゲーム読み込みが出来ません。ジャンク品です。"
        res = classify_condition(broken_text)
        self.assertTrue(res["is_broken"])
        self.assertEqual(res["condition_type"], "broken")
        self.assertIn("Uszkodzony", res["condition_badge"])

    def test_classify_condition_untested(self):
        untested_text = "充電器がない為動作未確認です。現状渡しとなります。"
        res = classify_condition(untested_text)
        self.assertFalse(res["is_broken"])
        self.assertTrue(res["is_untested"])
        self.assertEqual(res["condition_type"], "untested_opportunity")
        self.assertIn("Niesprawdzany", res["condition_badge"])

    def test_classify_condition_working(self):
        working_text = "動作確認済みです。ボタン操作良好、液晶綺麗です。"
        res = classify_condition(working_text)
        self.assertFalse(res["is_broken"])
        self.assertFalse(res["is_untested"])
        self.assertTrue(res["is_working"])
        self.assertEqual(res["condition_type"], "confirmed_working")

    def test_classify_condition_negation(self):
        negation_text = "液晶画面割れなし。ボタン故障はありません。美品。"
        res = classify_condition(negation_text)
        self.assertFalse(res["is_broken"])

    def test_landed_cost_calculation(self):
        # target item: 10,000 JPY
        # domestic shipping: 800 JPY -> 20.00 PLN (at 0.025)
        # zenmarket fee: 2 EUR -> 8.70 PLN (at 4.35)
        # base_purchase = 250.0 + 20.0 + 8.70 = 278.70 PLN
        # category "ps_vita" -> shipping_share = 35.0 PLN
        # subtotal = 278.70 + 35.0 = 313.70 PLN
        # deposit fee 3.5% = 10.98 PLN
        # vat 23% = 72.15 PLN
        # landed_cost = 278.70 + 35.0 + 10.98 + 72.15 = 396.83 PLN
        fallback = {"target_price_jpy": 10000, "est_pl_value": 800.0, "note": "Test Vita"}
        
        # Test with cached/fallback path (mocking urlopen to 404 to test fallback math)
        with patch("urllib.request.urlopen") as mock_open:
            import urllib.error
            mock_open.side_effect = urllib.error.HTTPError("url", 404, "Not Found", {}, None)
            res = self.fetcher.fetch_item_info("m1234567890", fallback, category_id="ps_vita")
            
            self.assertEqual(res["price_jpy"], 10000)
            self.assertEqual(res["price_pln_raw"], 250.0)
            self.assertEqual(res["shipping_share_pln"], 35.0)
            self.assertAlmostEqual(res["landed_cost_pln"], 396.83, places=2)
            self.assertAlmostEqual(res["est_margin_pln"], 800.0 - 396.83, places=2)
            self.assertGreater(res["roi_percent"], 100.0)
            self.assertEqual(res["status"], "Zakończone / 404")

    def test_url_construction(self):
        fallback = {"target_price_jpy": 5000}
        with patch("urllib.request.urlopen") as mock_open:
            mock_resp = MagicMock()
            mock_resp.read.return_value = b'<meta name="product:price:amount" content="5000"/><title>Test Console - Mercari</title>'
            mock_resp.__enter__.return_value = mock_resp
            mock_open.return_value = mock_resp

            res = self.fetcher.fetch_item_info("m999888777", fallback)
            self.assertEqual(res["mercari_url"], "https://jp.mercari.com/item/m999888777")
            self.assertEqual(res["zenmarket_url"], "https://zenmarket.jp/pl/mercariproduct.aspx?itemCode=m999888777")
            self.assertEqual(res["status"], "Dostępne")

    def test_sold_item_detection(self):
        fallback = {"target_price_jpy": 12000}
        with patch("urllib.request.urlopen") as mock_open:
            mock_resp = MagicMock()
            mock_resp.read.return_value = (
                b'<meta name="robots" content="noindex, follow"/>'
                b'<meta name="product:price:amount" content="12000"/>'
                b'<title>Sold Console - Mercari</title>'
            )
            mock_resp.__enter__.return_value = mock_resp
            mock_open.return_value = mock_resp

            res = self.fetcher.fetch_item_info("m111222333", fallback)
            self.assertEqual(res["status"], "Zakończone / Sprzedane")
            self.assertEqual(res["price_jpy"], 12000)

if __name__ == "__main__":
    unittest.main()
