import unittest
from unittest.mock import patch, MagicMock
from watcher.currency import get_live_nbp_rate, jpy_to_pln
from watcher.config import DEFAULT_JPY_PLN_RATE

class TestCurrency(unittest.TestCase):
    def test_jpy_to_pln_standard(self):
        # 10,000 JPY at rate 0.024832 = 248.32 PLN
        self.assertEqual(jpy_to_pln(10000, 0.024832), 248.32)

    def test_jpy_to_pln_edge_cases(self):
        self.assertEqual(jpy_to_pln(0, 0.025), 0.0)
        self.assertEqual(jpy_to_pln(-500, 0.025), 0.0)
        self.assertEqual(jpy_to_pln(None, 0.025), 0.0)

    @patch("urllib.request.urlopen")
    def test_get_live_nbp_rate_success(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"rates":[{"mid": 0.02495}]}'
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        rate, is_live = get_live_nbp_rate()
        self.assertTrue(is_live)
        self.assertEqual(rate, 0.02495)

    @patch("urllib.request.urlopen")
    def test_get_live_nbp_rate_fallback_on_error(self, mock_urlopen):
        mock_urlopen.side_effect = Exception("Connection timeout")

        rate, is_live = get_live_nbp_rate()
        self.assertFalse(is_live)
        self.assertEqual(rate, DEFAULT_JPY_PLN_RATE)

if __name__ == "__main__":
    unittest.main()
