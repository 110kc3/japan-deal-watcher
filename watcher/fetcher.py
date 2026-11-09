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
    DEFAULT_SHIPPING_SHARE_PLN,
    MAX_CAMERA_PRICE_PLN
)
from .costs import calculate_landed_cost
from .checks import (
    DEFECT_KEYWORDS,
    UNTESTED_KEYWORDS,
    CLEAN_OPTICS_KEYWORDS,
    CONFIRMED_WORKING_KEYWORDS,
    TRAP_KEYWORDS,
    is_camera_item
)

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
    c = item_condition or ""
    combined = (t + " " + n + " " + c).lower()

    # Pre-clean known future-disclaimer phrases and untested disclaimers
    cleaned = combined
    cleaned = cleaned.replace("ご購入後の故障", "")
    cleaned = cleaned.replace("購入後の故障", "")
    cleaned = cleaned.replace("早期の故障", "")
    cleaned = cleaned.replace("故障の可能性", "未確認")
    cleaned = cleaned.replace("故障している可能性", "未確認")

    # Negations for leaks, fungus, haze, abnormalities
    cleaned = cleaned.replace("カビなし", "カビ無し")
    cleaned = cleaned.replace("クモリなし", "クモリ無し")
    cleaned = cleaned.replace("傷なし", "傷無し")
    cleaned = cleaned.replace("電池液漏れ無", "液漏れなし")
    cleaned = cleaned.replace("液漏れ無", "液漏れなし")
    cleaned = cleaned.replace("異常無", "異常なし")

    # Check for empty box / trap keywords
    for trap in TRAP_KEYWORDS:
        if trap in cleaned:
            return {
                "is_broken": True,
                "is_untested": False,
                "is_working": False,
                "condition_type": "broken",
                "condition_badge": "❌ Pułapka Oferty (Tylko Pudełko)",
                "matched_flag": trap
            }

    # Exclusion check: Pentax PC35AF-M (user explicitly wants PC35AF manual thumbwheel, NOT motorized PC35AF-M)
    if any(unwanted in cleaned for unwanted in ["pc35af-m", "pc35afm", "pc35af m"]):
        return {
            "is_broken": True,
            "is_untested": False,
            "is_working": False,
            "condition_type": "broken",
            "condition_badge": "❌ Wykluczone: Model PC35AF-M (wymagany manualny PC35AF)",
            "matched_flag": "pc35af-m"
        }

    # If item is explicitly stated as untested because seller lacks cables/charger, prioritize untested
    is_explicit_untested = any(w in cleaned for w in [
        "動作未確認", "未確認", "充電器がない為動作未確認", "手元に電源コードやケーブル類がないため", "コードがないため", "確認していません"
    ])

    broken_keywords = sorted(list(DEFECT_KEYWORDS), key=len, reverse=True)
    if not is_explicit_untested:
        broken_keywords.append("部品取り")

    negations = ["なし", "ありません", "ないです", "確認済み", "無", "無し", "見られません", "ございません"]
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
    for kw in sorted(UNTESTED_KEYWORDS, key=len, reverse=True):
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
    for kw in CLEAN_OPTICS_KEYWORDS:
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
    for kw in CONFIRMED_WORKING_KEYWORDS:
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
        self.rate_jpy = float(rate)
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
        image_url = fallback_info.get("image_url") if fallback_info else None
        raw_description = fallback_info.get("note", "") if fallback_info else ""
        item_condition = ""

        is_mercari_id = bool(re.match(r"^m\d+$", str(item_id)))
        if not is_mercari_id:
            # Non-Mercari tracked item (e.g. curated proxy stream or test lot)
            cost_info = calculate_landed_cost(
                price_jpy=price_jpy,
                category_id=category_id,
                rate_jpy=self.rate_jpy,
                rate_eur=self.rate_eur
            )
            est_pl = float(fallback_info.get("est_pl_value", 0)) if fallback_info else 0.0
            margin = round(est_pl - cost_info["landed_cost_pln"], 2)
            roi = round((margin / cost_info["landed_cost_pln"] * 100.0), 1) if cost_info["landed_cost_pln"] > 0 else 0.0
            
            # Avoid leaking internal IDs into search URLs
            search_q = fallback_info.get("search_query_jp") or fallback_info.get("model", "") if fallback_info else ""
            encoded_q = urllib.parse.quote(search_q)
            zenmarket_url = fallback_info.get("zenmarket_url") if fallback_info else ""
            if not zenmarket_url:
                zenmarket_url = f"https://zenmarket.jp/pl/yahoo.aspx?q={encoded_q}"
            mercari_url = fallback_info.get("source_url") if fallback_info else ""
            if not mercari_url:
                mercari_url = f"https://jp.mercari.com/search?keyword={encoded_q}&status=on_sale"

            return {
                "id": item_id,
                "title": fallback_info.get("model", title) if fallback_info else title,
                "price_jpy": price_jpy,
                "price_pln_raw": cost_info["price_pln_raw"],
                "landed_cost_pln": cost_info["landed_cost_pln"],
                "est_pl_value": est_pl,
                "est_margin_pln": margin,
                "roi_percent": roi,
                "status": "Dostępne",
                "image_url": image_url,
                "description": raw_description,
                "condition_type": "confirmed_working",
                "condition_badge": "🟢 0% Li-Ion (Zero Baterii)",
                "is_broken": False,
                "is_untested": False,
                "shipping_share_pln": cost_info["shipping_share_pln"],
                "vat_pln": cost_info["vat_pln"],
                "zenmarket_fee_pln": cost_info["zenmarket_fee_pln"],
                "zenmarket_url": zenmarket_url,
                "mercari_url": mercari_url,
                "search_query_jp": search_q,
                "category_id": category_id,
                "battery_type": fallback_info.get("battery_type", "none") if fallback_info else "none",
                "photo_inspection": fallback_info.get("photo_inspection") if fallback_info else None
            }

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
                err_msg = str(e)
                if "KeyError" in type(e).__name__ or "data" in err_msg or "404" in err_msg or "400" in err_msg:
                    logging.info(f"Item {item_id} confirmed non-existent / 404 via Mercapi ({e}).")
                    status = "Zakończone / 404"
                    checked_via_mercapi = True
                else:
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
                        
                        # Check title
                        t_match = re.search(r'<title>(.*?)</title>', html)
                        clean_title = ""
                        if t_match:
                            clean_title = t_match.group(1).split("-")[0].strip()

                        # Check image
                        img_match = re.search(r'<meta property=[\"\']og:image[\"\'] content=[\"\']([^\"\']+)[\"\']', html)
                        if img_match:
                            image_url = img_match.group(1)

                        # Check description
                        desc_match = re.search(r'<meta property=[\"\']og:description[\"\'] content=[\"\']([^\"\']+)[\"\']', html)
                        if desc_match:
                            raw_description = desc_match.group(1)

                        is_sold = bool(
                            re.search(r'<meta[^>]*robots[^>]*noindex', html, re.IGNORECASE) or
                            "売り切れ" in html or
                            "item-status:sold-out" in html
                        )

                        if p_match:
                            price_jpy = int(p_match.group(1))
                            if clean_title and clean_title != "メルカリ":
                                title = clean_title
                            if is_sold:
                                status = "Zakończone / Sprzedane"
                            else:
                                status = "Dostępne"
                        else:
                            # SPA shell without product data: item is dead/removed
                            status = "Zakończone / 404"
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
            "search_query_jp": fallback_info.get("search_query_jp", "") if fallback_info else "",
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
