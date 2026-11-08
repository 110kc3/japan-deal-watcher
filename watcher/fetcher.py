"""Fetcher module to verify Mercari Japan listings and calculate landed costs."""

import urllib.request
import re
import json
import logging
from .config import (
    USER_AGENT,
    REQUEST_TIMEOUT,
    DEFAULT_JPY_PLN_RATE,
    ZENMARKET_FEE_JPY,
    VAT_RATE,
    CATEGORY_SHIPPING_SHARES,
    DEFAULT_SHIPPING_SHARE_PLN
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

try:
    import asyncio
    from mercapi import Mercapi
    _HAS_MERCAPI = True
except ImportError:
    _HAS_MERCAPI = False


class DealFetcher:
    def __init__(self, rate=DEFAULT_JPY_PLN_RATE, enable_mercapi=True):
        self.rate = float(rate)
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

        # Calculate landed cost in Poland
        total_jpy = max(0, price_jpy) + ZENMARKET_FEE_JPY
        base_pln = total_jpy * self.rate
        
        # Category-aware shipping share
        shipping_share_pln = CATEGORY_SHIPPING_SHARES.get(category_id, DEFAULT_SHIPPING_SHARE_PLN)
        
        # VAT 23%
        vat_pln = (base_pln + shipping_share_pln) * VAT_RATE
        landed_cost_pln = round(base_pln + shipping_share_pln + vat_pln, 2)

        est_pl_value = float(fallback_info.get("est_pl_value", landed_cost_pln * 1.5)) if fallback_info else landed_cost_pln * 1.5
        est_margin_pln = round(est_pl_value - landed_cost_pln, 2)
        roi_percent = round((est_margin_pln / landed_cost_pln) * 100, 1) if landed_cost_pln > 0 else 0

        return {
            "id": item_id,
            "title": title,
            "price_jpy": price_jpy,
            "price_pln_raw": round(price_jpy * self.rate, 2),
            "shipping_share_pln": shipping_share_pln,
            "landed_cost_pln": landed_cost_pln,
            "est_pl_value": est_pl_value,
            "est_margin_pln": est_margin_pln,
            "roi_percent": roi_percent,
            "status": status,
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
                details["battery_type"] = battery_type
                details["model"] = item.get("model", "")
                details["color"] = item.get("color", "")
                details["custom_note"] = item.get("note", "")
                results.append(details)
                
        return results
