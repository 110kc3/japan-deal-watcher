"""Fetcher module to verify Mercari Japan listings and calculate landed costs."""

import urllib.request
import re
import json
import logging
from .config import (
    USER_AGENT,
    REQUEST_TIMEOUT,
    DEFAULT_JPY_PLN_RATE,
    DEFAULT_EUR_PLN_RATE,
    ZENMARKET_FEE_JPY,
    ZENMARKET_FEE_EUR,
    ZENMARKET_DEPOSIT_FEE_RATE,
    VAT_RATE,
    CATEGORY_SHIPPING_SHARES,
    DEFAULT_SHIPPING_SHARE_PLN
)
from .costs import calculate_landed_cost

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

try:
    import asyncio
    from mercapi import Mercapi
    _HAS_MERCAPI = True
except ImportError:
    _HAS_MERCAPI = False


def classify_condition(text, item_condition="", custom_note=""):
    """
    Analyzes item description, title, Mercari condition grade, and custom note:
    - 'broken': explicit defects (broken disk drive, cracked LCD, won't turn on, for parts only).
    - 'untested_opportunity': untested/not checked/no charger (high gain potential!).
    - 'confirmed_working': verified operational.
    - 'lens_clean': clean retro optics.
    """
    t = text or ""
    n = custom_note or ""
    combined = (t + " " + n).lower()

    # Pre-clean known future-disclaimer phrases and untested disclaimers
    cleaned = combined
    cleaned = cleaned.replace("ご購入後の故障", "")
    cleaned = cleaned.replace("購入後の故障", "")
    cleaned = cleaned.replace("早期の故障", "")
    cleaned = cleaned.replace("故障の可能性", "未確認")
    cleaned = cleaned.replace("故障している可能性", "未確認")

    # Negations for leaks and abnormalities
    cleaned = cleaned.replace("電池液漏れ無", "液漏れなし")
    cleaned = cleaned.replace("液漏れ無", "液漏れなし")
    cleaned = cleaned.replace("異常無", "異常なし")

    # If item is explicitly stated as untested because seller lacks cables/charger, prioritize untested
    is_explicit_untested = any(w in cleaned for w in [
        "動作未確認", "未確認", "充電器がない為動作未確認", "手元に電源コードやケーブル類がないため", "コードがないため", "確認していません"
    ])

    # 1. Defect & Broken detection (exclusion filter)
    broken_keywords = [
        "故障", "壊れて", "壊れ", "動かない", "動作不可", "作動不可",
        "起動不可", "起動しません", "起動しない", "電源入りません", "電源つかない", "電源が入らない",
        "画面割れ", "液晶割れ", "液晶漏れ", "液漏れ", "バックライト切れ",
        "水没", "不動品",
        "読み込みが出来ません", "読み込み不可", "読み込まない", "ディスク読み込まない",
        "スティック誤作動", "スティックドリフト",
        "破損しており", "破損あり"
    ]
    # If not explicitly marked as untested due to lack of cables, also check for parts-only flag
    if not is_explicit_untested:
        broken_keywords.append("部品取り")

    negations = ["なし", "ありません", "ないです", "確認済み", "無", "無し"]
    for kw in broken_keywords:
        if kw in cleaned:
            is_negated = any(kw + neg in cleaned or kw + "は" + neg in cleaned for neg in negations)
            if not is_negated:
                return {
                    "is_broken": True,
                    "is_untested": False,
                    "is_working": False,
                    "condition_type": "broken",
                    "condition_badge": "❌ Uszkodzony (Wykluczone)",
                    "matched_flag": kw
                }

    # 2. Untested / Not Checked detection (POTENTIAL FOR GAIN)
    untested_keywords = [
        "未確認", "動作未確認", "動作未チェック", "未チェック",
        "現状品", "現状渡し", "通電のみ", "通電確認のみ", "通電ok",
        "確認していません", "確認しておりません", "動作確認はしておりません", "確認できておりません",
        "充電器がない", "環境がない", "ソフトがない", "コードがない", "未検品"
    ]
    for kw in untested_keywords:
        if kw in cleaned:
            return {
                "is_broken": False,
                "is_untested": True,
                "is_working": False,
                "condition_type": "untested_opportunity",
                "condition_badge": "⚡ Niesprawdzany (Potencjał Zysku)",
                "matched_flag": kw
            }

    # 3. Vintage optics clean detection
    lens_keywords = ["光学クリア", "カビなし", "クモリなし", "分解清掃", "黄変除去", "dry box", "防湿box"]
    for kw in lens_keywords:
        if kw in combined:
            return {
                "is_broken": False,
                "is_untested": False,
                "is_working": True,
                "condition_type": "lens_clean",
                "condition_badge": "💎 Czysta Optyka",
                "matched_flag": kw
            }

    # 4. Confirmed working detection
    working_keywords = [
        "動作確認済み", "動作確認済", "動作品", "完動品", "動作ok",
        "起動確認", "初期化済", "ボタン正常", "読み込みok", "液晶良好",
        "美品", "良品", "整備済", "メンテナンス済", "新品バッテリー"
    ]
    for kw in working_keywords:
        if kw in combined:
            return {
                "is_broken": False,
                "is_untested": False,
                "is_working": True,
                "condition_type": "confirmed_working",
                "condition_badge": "✅ Sprawny (Potwierdzone)",
                "matched_flag": kw
            }

    return {
        "is_broken": False,
        "is_untested": False,
        "is_working": True,
        "condition_type": "standard_good",
        "condition_badge": "✅ Stan Dobry",
        "matched_flag": None
    }


class DealFetcher:
    def __init__(self, rate=DEFAULT_JPY_PLN_RATE, rate_eur=DEFAULT_EUR_PLN_RATE, enable_mercapi=True):
        self.rate = float(rate)
        self.rate_eur = float(rate_eur)
        self.headers = {"User-Agent": USER_AGENT}
        self.enable_mercapi = enable_mercapi and _HAS_MERCAPI
        self.mercapi_client = Mercapi() if self.enable_mercapi else None
        self._loop = None

    def _get_loop(self):
        if self._loop is None or self._loop.is_closed():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
        return self._loop

    def fetch_item_info(self, item_id, fallback_info=None, category_id=None):
        """
        Inspects live Mercari item using official/signed API when available,
        falling back to HTTP scraping. Extracts exact live status: 'on_sale' vs 'sold_out' / 'trading'.
        """
        title = fallback_info.get("note", "Przedmiot Mercari") if fallback_info else "Przedmiot Mercari"
        price_jpy = fallback_info.get("target_price_jpy", 0) if fallback_info else 0
        status = "Active"
        image_url = None
        raw_description = ""
        item_condition = ""

        checked_via_mercapi = False

        if self.enable_mercapi and self.mercapi_client:
            try:
                loop = self._get_loop()
                item_data = loop.run_until_complete(self.mercapi_client.item(item_id))
                checked_via_mercapi = True

                if item_data is None:
                    status = "Zakończone / 404"
                else:
                    if item_data.name:
                        title = item_data.name
                    if item_data.price:
                        price_jpy = item_data.price
                    if item_data.thumbnails:
                        image_url = item_data.thumbnails[0]
                    if item_data.description:
                        raw_description = item_data.description
                    if item_data.item_condition and item_data.item_condition.name:
                        item_condition = item_data.item_condition.name

                    raw_status = str(item_data.status).lower()
                    if "on_sale" in raw_status:
                        status = "Dostępne"
                    elif "trading" in raw_status:
                        status = "W trakcie transakcji"
                    elif "sold" in raw_status:
                        status = "Zakończone / Sprzedane"
                    else:
                        status = f"Status: {raw_status}"

            except Exception as e:
                logging.debug(f"Mercapi check for {item_id} failed: {e}. Falling back to HTTP.")
                checked_via_mercapi = False

        if not checked_via_mercapi:
            url = f"https://jp.mercari.com/item/{item_id}"
            req = urllib.request.Request(url, headers=self.headers)
            max_attempts = 2
            for attempt in range(max_attempts):
                try:
                    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                        html = resp.read().decode("utf-8")
                        
                        # Check price
                        p_match = re.search(r'product:price:amount\"\s*content=\"(\d+)\"', html)
                        if p_match:
                            price_jpy = int(p_match.group(1))

                        # Check title
                        t_match = re.search(r'<title>(.*?)</title>', html)
                        if t_match:
                            clean_title = t_match.group(1).split("-")[0].strip()
                            if clean_title and clean_title != "メルカリ":
                                title = clean_title

                        # Check image
                        img_match = re.search(r'<meta property=[\"\']og:image[\"\'] content=[\"\']([^\"\']+)[\"\']', html)
                        if img_match:
                            image_url = img_match.group(1)

                        # Check description
                        desc_match = re.search(r'<meta property=[\"\']og:description[\"\'] content=[\"\']([^\"\']+)[\"\']', html)
                        if desc_match:
                            raw_description = desc_match.group(1)

                        is_sold = bool(re.search(r'<meta[^>]*robots[^>]*noindex', html, re.IGNORECASE))
                        if is_sold:
                            status = "Zakończone / Sprzedane"
                        elif price_jpy > 0:
                            status = "Dostępne"
                        else:
                            status = "Niedostępne"
                        break

                except urllib.error.HTTPError as e:
                    if e.code == 404:
                        logging.warning(f"Item {item_id} returned 404 (Sold / Removed).")
                        status = "Zakończone / 404"
                        break
                    else:
                        logging.warning(f"Item {item_id} HTTP error: {e}")
                        status = f"Błąd HTTP {e.code}"
                        if attempt == max_attempts - 1:
                            break
                except Exception as e:
                    if attempt == max_attempts - 1:
                        logging.warning(f"Could not reach {item_id}: {e}.")
                        status = "Błąd połączenia"

        # Analyze description and condition
        custom_note = fallback_info.get("note", "") if fallback_info else ""
        cond_info = classify_condition(raw_description + " " + title, item_condition=item_condition, custom_note=custom_note)
        is_broken = cond_info["is_broken"]
        if is_broken:
            status = "Wykluczone: Uszkodzone (Broken)"

        # Calculate landed cost in Poland with full fee itemization
        cost_info = calculate_landed_cost(
            price_jpy=price_jpy,
            category_id=category_id,
            rate_jpy=self.rate,
            rate_eur=self.rate_eur
        )
        landed_cost_pln = cost_info["landed_cost_pln"]
        shipping_share_pln = cost_info["shipping_share_pln"]
        price_pln_raw = cost_info["price_pln_raw"]

        est_pl_value = float(fallback_info.get("est_pl_value", landed_cost_pln * 1.5)) if fallback_info else landed_cost_pln * 1.5
        est_margin_pln = round(est_pl_value - landed_cost_pln, 2)
        roi_percent = round((est_margin_pln / landed_cost_pln) * 100, 1) if landed_cost_pln > 0 else 0

        return {
            "id": item_id,
            "title": title,
            "price_jpy": price_jpy,
            "price_pln_raw": price_pln_raw,
            "domestic_shipping_pln": cost_info["domestic_shipping_pln"],
            "zenmarket_fee_pln": cost_info["zenmarket_fee_pln"],
            "deposit_fee_pln": cost_info["deposit_fee_pln"],
            "vat_pln": cost_info["vat_pln"],
            "shipping_share_pln": shipping_share_pln,
            "landed_cost_pln": landed_cost_pln,
            "est_pl_value": est_pl_value,
            "est_margin_pln": est_margin_pln,
            "roi_percent": roi_percent,
            "status": status,
            "condition_type": cond_info["condition_type"],
            "condition_badge": cond_info["condition_badge"],
            "is_broken": is_broken,
            "is_untested": cond_info["is_untested"],
            "is_working": cond_info["is_working"],
            "matched_flag": cond_info["matched_flag"],
            "description_snippet": raw_description[:160].replace("\n", " ").strip() if raw_description else "",
            "image_url": image_url,
            "mercari_url": f"https://jp.mercari.com/item/{item_id}",
            "zenmarket_url": f"https://zenmarket.jp/pl/mercariproduct.aspx?itemCode={item_id}"
        }

    def scan_watchlist(self, watchlist_data):
        """
        Scans all categories and items in watchlist.
        """
        results = []
        for cat in watchlist_data.get("categories", []):
            cat_id = cat.get("id")
            cat_name = cat.get("name")
            battery_type = cat.get("battery_type", "none")
            
            for item in cat.get("tracked_items", []):
                item_id = item.get("id")
                logging.info(f"Scanning [{cat_name}] Item {item_id}...")
                details = self.fetch_item_info(item_id, item, category_id=cat_id)
                details["category_id"] = cat_id
                details["category_name"] = cat_name
                details["battery_type"] = item.get("battery_type", battery_type)
                details["model"] = item.get("model", "")
                details["color"] = item.get("color", "")
                details["custom_note"] = item.get("note", "")
                results.append(details)
                
        return results
