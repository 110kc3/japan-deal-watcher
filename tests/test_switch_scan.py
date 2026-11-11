"""Regression checks for separating real console offers from misleading search hits."""
import unittest
from scripts.scan_switch_offers import condition, matches_category, parse_yahoo_search, report


class SwitchScanTests(unittest.TestCase):
    def test_models_are_separate_and_accessories_are_not_consoles(self):
        cases = [
            ('Nintendo Switch Lite 本体 グレー', 'nintendo_switch_lite', True),
            ('Nintendo Switch Lite 本体 グレー', 'nintendo_switch', False),
            ('Nintendo Switch 有機EL 本体', 'nintendo_switch', True),
            ('Nintendo Switch ２ 本体', 'nintendo_switch', False),
            ('Nintendo Switch Lite 本体 カバー', 'nintendo_switch_lite', False),
            ('スイッチライト ケース', 'nintendo_switch_lite', False),
            ('Nintendo Switch 外箱のみ', 'nintendo_switch', False),
            ('Nintendo DS Lite 本体', 'nintendo_switch_lite', False),
        ]
        for title, category, expected in cases:
            with self.subTest(title=title, category=category):
                self.assertEqual(matches_category(title, category), expected)

    def test_defects_override_claims_and_negation_is_local(self):
        for text in ['動作確認済み。液晶が少し壊れている', '動作確認済み。充電出来ません',
                     'ボタンの接触不良なし。Joy-Conは極稀に接触不良があります',
                     '動作確認済み。修理が必要', '動作確認済み。液晶画面に線が入っています']:
            with self.subTest(text=text):
                self.assertEqual(condition(text)[0], 'defect_reported')
        self.assertEqual(condition('ボタンの接触不良なし。充電等動作確認済み')[0], 'seller_claims_working')
        self.assertEqual(condition('動作確認済みですが、Joy-Conは未確認です')[0], 'untested_or_partial')
        self.assertEqual(condition('美品、初期化済み')[0], 'unknown')

    def test_search_price_is_not_a_final_price_or_exact_deadline(self):
        body = '''<a href="https://www.jauce.com/auction/../auction/a1234567890">
        <img src="https://example.com/test.jpg" alt="Nintendo Switch Lite 本体 &amp; 箱">
        Bid: 1,234 yen Time left: 12hour(s)</a>'''
        rows = parse_yahoo_search(body, 'nintendo_switch_lite', 'https://www.jauce.com/search/test')
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['price_jpy'], 1234)
        self.assertEqual(rows[0]['price_type'], 'current_bid')
        self.assertEqual(rows[0]['time_left_observed'], '12hour(s)')
        self.assertEqual(rows[0]['evidence'], 'search_result_only')
        self.assertNotIn('ends_at', rows[0])
        self.assertIn('& 箱', rows[0]['title'])
        self.assertEqual(parse_yahoo_search('<html>captcha</html>', 'nintendo_switch', 'https://example.com'), [])

    def test_report_does_not_claim_inspected_auctions_or_resale_profit(self):
        output = report({'observed_at': '2026-11-11T23:30:00+00:00', 'offers': [], 'rejected': [], 'errors': []})
        self.assertIn('pełny opis niezweryfikowany', output)
        self.assertIn('nie ofertą przewoźnika ani wyceną odsprzedaży', output)
        self.assertIn('Brak kandydatów z tego skanu', output)


if __name__ == '__main__':
    unittest.main()
