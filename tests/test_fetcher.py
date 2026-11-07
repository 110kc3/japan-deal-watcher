import unittest
from unittest.mock import patch, MagicMock
from watcher.fetcher import DealFetcher

class TestFetcher(unittest.TestCase):
    def setUp(self):
        self.fetcher = DealFetcher(rate=0.025)

    def test_landed_cost_calculation(self):
        # target item: 10,000 JPY
        # zenmarket fee: 500 JPY -> total 10,500 JPY
        # base_pln = 10,500 * 0.025 = 262.5 PLN
        # category "ps_vita" -> shipping_share = 35.0 PLN
        # vat = (262.5 + 35.0) * 0.23 = 68.425 PLN
        # landed_cost = 262.5 + 35.0 + 68.425 = 365.925 -> 365.93 PLN
        fallback = {"target_price_jpy": 10000, "est_pl_value": 800.0, "note": "Test Vita"}
        
        # Test with cached/fallback path (mocking urlopen to 404 to test fallback math)
        with patch("urllib.request.urlopen") as mock_open:
            import urllib.error
            mock_open.side_effect = urllib.error.HTTPError("url", 404, "Not Found", {}, None)
            res = self.fetcher.fetch_item_info("m1234567890", fallback, category_id="ps_vita")
            
            self.assertEqual(res["price_jpy"], 10000)
            self.assertEqual(res["price_pln_raw"], 250.0)
            self.assertEqual(res["shipping_share_pln"], 35.0)
            self.assertAlmostEqual(res["landed_cost_pln"], 365.93, places=2)
            self.assertAlmostEqual(res["est_margin_pln"], 800.0 - 365.93, places=2)
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
