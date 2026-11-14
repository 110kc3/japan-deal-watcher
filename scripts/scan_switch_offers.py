#!/usr/bin/env python3
"""Bounded Switch research scan. Never fabricates listings, bids, end dates or resale values."""
import argparse
import asyncio
import html
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unicodedata
import urllib.parse
import urllib.request
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from mercapi import Mercapi
from mercapi.requests.search import SearchRequestData as Search
from watcher.config import USER_AGENT
from watcher.costs import calculate_landed_cost
from watcher.currency import get_live_rates
from watcher.storage import atomic_write_json

CATEGORIES = {
    'nintendo_switch_lite': ('Nintendo Switch Lite', 703, 'Switch Lite'),
    'nintendo_switch': ('Nintendo Switch', 701, 'Switch'),
}
REPORT_FILES = ['reports/switch-offers.json', 'reports/switch-offers.md']
TRAPS = re.compile(r'箱のみ|空箱|ケース|カバー|フィルム|交換用|シェル|基板|ソフトのみ|ドックのみ|充電器のみ|専用出品', re.I)
DEFECTS = re.compile(r'ジャンク|ジャング品|訳あり|難あり|壊れ|故障|修理が必要|変形|湾曲|ひび割れ|ヒビ|割れて|'
                     r'読み込みにくい|充電(?:が)?(?:出来|でき)(?:ない|ません)|'
                     r'(?:画面|液晶)[^。\n]{0,12}線が|(?:接触|動作|充電|液晶|ボタン)不良|'
                     r'スティック[^。\n]{0,12}(?:取れ|切れ|ドリフト)', re.I)
WORKING = re.compile(r'動作確認済|動作品|完動品|動作OK|稼動品|動作は問題', re.I)
UNTESTED = re.compile(r'未確認|確認していない|起動確認のみ|初期設定画面|すべてのボタン[^。]{0,20}チェック', re.I)

def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')

def matches_category(title, category):
    text = unicodedata.normalize('NFKC', title)
    if not re.search(r'switch|スイッチ', text, re.I):
        return False
    if re.search(r'(?:switch|スイッチ)\s*2', text, re.I) or TRAPS.search(text):
        return False
    is_lite = bool(re.search(r'lite|ライト', text, re.I))
    if is_lite != (category == 'nintendo_switch_lite'):
        return False
    return bool(re.search(r'本体|HDH[- ]?001|HAC[- ]?001|Nintendo\s*Switch|ニンテンドー\s*スイッチ', text, re.I))

def condition(text):
    clean = re.sub(r'(?:接触|動作|充電|液晶|ボタン)不良(?:なし|無し|はありません)', '', text)
    defect = DEFECTS.search(clean)
    if defect:
        return 'defect_reported', defect.group(0)
    if UNTESTED.search(text):
        return 'untested_or_partial', 'Brak pełnego testu / tylko częściowy test'
    if WORKING.search(text):
        return 'seller_claims_working', 'Sprzedawca deklaruje sprawność'
    return 'unknown', 'Brak jednoznacznej deklaracji testu'

def observations(text):
    notes = []
    checks = [
        (r'本体のみ', 'Sama konsola/tablet; sprawdź komplet akcesoriów'),
        (r'Joy-Conなし|ジョイコンはありません|ジョイコンなし', 'Bez Joy-Conów'),
        (r'充電器.{0,8}(?:なし|無し|付いておりません|付きません)|充電器・ドック', 'Sprawdź brak ładowarki/docka'),
        (r'シリアルナンバー剥', 'Usunięta naklejka z numerem seryjnym'),
        (r'スティックカバーなし|ラバー欠品', 'Brak nakładki na gałkę'),
        (r'黄ば|黄色がか', 'Przebarwienie ekranu'),
        (r'傷|擦れ|摩耗', 'Opis zawiera ślady używania/rysy'),
        (r'着払い', 'Dostawa krajowa płatna przez kupującego'),
    ]
    for pattern, note in checks:
        if re.search(pattern, text, re.I):
            notes.append(note)
    return notes

def parse_yahoo_search(body, category, source_url):
    pattern = re.compile(
        r'href=["\x27]https://www\.jauce\.com/auction/\.\./auction/([a-zA-Z]\d+)["\x27][^>]*>.*?'
        r'<img\s+src=["\x27](?:/read_yafile/)?([^"\x27]+)["\x27]\s+alt=["\x27]([^"\x27]+)["\x27].*?'
        r'Bid:\s*([0-9,]+)\s*yen.*?Time left:\s*([^<\n]+)', re.S)
    rows = []
    for aid, image_url, title, bid, time_left in pattern.findall(body):
        title = html.unescape(title).strip()
        rows.append({'id': aid, 'category_id': category, 'source': 'yahoo', 'title': title,
                     'price_jpy': int(bid.replace(',', '')), 'price_type': 'current_bid',
                     'time_left_observed': time_left.strip(), 'observed_at': now_iso(),
                     'evidence': 'search_result_only', 'source_search_url': source_url,
                     'source_url': f'https://page.auctions.yahoo.co.jp/jp/auction/{aid}',
                     'proxy_url': f'https://zenmarket.jp/pl/auction.aspx?itemCode={aid}'})
    return rows

def yahoo_search(category):
    query = CATEGORIES[category][0] + ' 本体'
    url = 'https://www.jauce.com/search/' + urllib.parse.quote(query)
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as response:
        body = response.read().decode('utf-8', errors='replace')
    rows = parse_yahoo_search(body, category, url)
    if not rows:
        raise RuntimeError('Brak rozpoznanych wyników; możliwa zmiana strony lub blokada')
    return rows

async def scan():
    result = {'observed_at': now_iso(), 'queries': [], 'offers': [], 'rejected': [], 'errors': []}
    rate_jpy, rate_eur, live_jpy, live_eur = get_live_rates()
    result['rates'] = {'jpy_pln': rate_jpy, 'eur_pln': rate_eur, 'nbp_fetch_ok': live_jpy and live_eur}
    mercari = Mercapi()
    for category, (_, category_number, query) in CATEGORIES.items():
        try:
            rows = await asyncio.to_thread(yahoo_search, category)
            result['queries'].append({'source': 'yahoo', 'category_id': category, 'result_count': len(rows)})
            for row in rows:
                if not matches_category(row['title'], category):
                    continue
                state, label = condition(row['title'])
                row.update(condition_status=state, condition_note=label, notes=observations(row['title']))
                if state == 'defect_reported':
                    result['rejected'].append(row)
                else:
                    result['offers'].append(row)
        except Exception as exc:
            result['errors'].append({'source': 'yahoo', 'category_id': category, 'error': str(exc)})
        try:
            search = await asyncio.wait_for(mercari.search(
                query, categories=[category_number], status=[Search.Status.STATUS_ON_SALE],
                sort_by=Search.SortBy.SORT_SCORE, price_min=6000, price_max=23000,
                exclude='ジャンク ソフト ケース フィルム 部品 交換用'), timeout=30)
            result['queries'].append({'source': 'mercari', 'category_id': category,
                                      'result_count': len(search.items), 'price_window_jpy': [6000, 23000]})
            candidates = [item for item in search.items if re.fullmatch(r'm\d+', item.id_)
                          and matches_category(item.name, category)
                          and not (item.auction and item.auction.id_)]
            for candidate in sorted(candidates, key=lambda item: item.price)[:24]:
                try:
                    item = await asyncio.wait_for(mercari.item(candidate.id_), timeout=15)
                    if not item or item.status != 'on_sale' or not matches_category(item.name, category):
                        continue
                    if item.auction_info and getattr(item.auction_info, 'id_', None):
                        continue
                    if not isinstance(item.price, int) or item.price <= 0:
                        continue
                    text = item.name + '\n' + (item.description or '')
                    state, label = condition(text)
                    row = {'id': item.id_, 'category_id': category, 'source': 'mercari',
                           'title': item.name, 'price_jpy': item.price, 'price_type': 'fixed_price',
                           'observed_at': now_iso(), 'availability': item.status,
                           'evidence': 'item_detail', 'condition_status': state, 'condition_note': label,
                           'notes': observations(text), 'shipping_payer': item.shipping_payer.name,
                           'source_url': f'https://jp.mercari.com/item/{item.id_}',
                           'proxy_url': f'https://zenmarket.jp/pl/mercariproduct.aspx?itemCode={item.id_}'}
                    result['rejected' if state == 'defect_reported' else 'offers'].append(row)
                except Exception as exc:
                    result['errors'].append({'source': 'mercari', 'id': candidate.id_, 'error': str(exc)})
        except Exception as exc:
            result['errors'].append({'source': 'mercari', 'category_id': category, 'error': str(exc)})
    unique = {(row['source'], row['id']): row for row in result['offers']}
    result['offers'] = list(unique.values())
    for row in result['offers']:
        costs = calculate_landed_cost(row['price_jpy'], row['category_id'], rate_jpy, rate_eur)
        row['price_pln'] = costs['price_pln_raw']
        row['model_landed_pln'] = costs['landed_cost_pln']
    return result

def report(data):
    lines = ['# Switch i Switch Lite — przegląd ofert', '', f"Sprawdzenie UTC: {data['observed_at']}", '',
             'Mercari: cena i dostępność odczytane z karty przedmiotu. Sprawność to deklaracja sprzedawcy, nie test urządzenia.',
             'Yahoo: cena bieżącej licytacji i przybliżony czas z wyników Jauce; pełny opis niezweryfikowany. Cena końcowa może wzrosnąć.',
             'Zakres Mercari: wyniki trafności 6 000–23 000 JPY, maks. 24 tańsze karty na kategorię; to nie pełny przegląd rynku.',
             'Koszt PL jest scenariuszem z istniejącego kalkulatora (opłaty, VAT i szacowany udział przesyłki), nie ofertą przewoźnika ani wyceną odsprzedaży.', '',
             f"Wynik: {len(data['offers'])} kandydatów; {len(data['rejected'])} odrzuconych po wykryciu wady w tytule/opisie; {len(data['errors'])} błędów źródeł.", '']
    def safe(value):
        return (html.escape(str(value)).replace('|', '\\|').replace('\n', ' ')
                .replace('[', '\\[').replace(']', '\\]'))
    for source, source_name in [('mercari', 'Kup teraz — Mercari'), ('yahoo', 'Aukcje — Yahoo')]:
        for category, (name, _, _) in CATEGORIES.items():
            rows = [r for r in data['offers'] if r['source'] == source and r['category_id'] == category]
            rows.sort(key=lambda r: (r['condition_status'] != 'seller_claims_working', r['price_jpy']))
            lines += [f'## {name}: {source_name}', '', '| Oferta | JPY | Sam zakup PLN | Model kosztu PL | Stan / uwagi |', '|---|---:|---:|---:|---|']
            for row in rows[:8]:
                notes = '; '.join([row['condition_note'], *row['notes']])
                if source == 'yahoo':
                    notes += '; czas w wynikach: ' + row['time_left_observed']
                lines.append(f"| [{safe(row['title'])}]({row['source_url']}) · [ZenMarket]({row['proxy_url']}) | {row['price_jpy']:,} | {row['price_pln']:.2f} | {row['model_landed_pln']:.2f} | {safe(notes)} |")
            if not rows:
                lines.append('| Brak kandydatów z tego skanu | — | — | — | Sprawdź błędy źródeł |')
            lines.append('')
    if data['errors']:
        lines += ['## Dostępność źródeł', ''] + [f"- {safe(error)}" for error in data['errors']]
    lines += ['', 'Pełne wyniki i identyfikatory odrzuconych ofert: [switch-offers.json](switch-offers.json).', '']
    return '\n'.join(lines)

def write_reports(destination):
    data = asyncio.run(scan())
    if not data['offers']:
        raise RuntimeError('Nie uzyskano żadnych kandydatów; poprzedni raport pozostaje zachowany')
    destination.mkdir(parents=True, exist_ok=True)
    atomic_write_json(destination / 'switch-offers.json', data)
    temporary = destination / '.switch-offers.md.tmp'
    temporary.write_text(report(data), encoding='utf-8')
    temporary.replace(destination / 'switch-offers.md')
    print(json.dumps({'offers': len(data['offers']), 'rejected': len(data['rejected']), 'errors': len(data['errors'])}))

def publish():
    """Publish only research files from an isolated clone; never touch the shared index."""
    def git(*args, cwd=ROOT):
        return subprocess.check_output(['git', *args], cwd=cwd, text=True, timeout=120).strip()
    remote = git('remote', 'get-url', 'origin')
    checkout = Path(tempfile.mkdtemp(prefix='jdw-switch-scheduled-'))
    print(f'Isolated report checkout: {checkout}', flush=True)
    git('clone', '--quiet', '--depth=1', '--branch', 'main', remote, str(checkout))
    write_reports(checkout / 'reports')
    git('add', '--', *REPORT_FILES, cwd=checkout)
    if not git('diff', '--cached', '--name-only', cwd=checkout):
        return
    git('-c', 'user.name=Codex', '-c', 'user.email=codex@users.noreply.github.com',
        'commit', '-m', 'chore: refresh Switch offer research [skip ci]', cwd=checkout)
    git('fetch', 'origin', 'main', cwd=checkout)
    git('rebase', 'origin/main', cwd=checkout)
    git('push', 'origin', 'HEAD:main', cwd=checkout)
    print('Published: ' + git('rev-parse', 'HEAD', cwd=checkout), flush=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--publish', action='store_true', help='Scan and publish research only from an isolated clone')
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'reports')
    args = parser.parse_args()
    publish() if args.publish else write_reports(args.output_dir)
