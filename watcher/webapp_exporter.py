"""Exporter module for compiling Web App JSON data feed (Android PWA on GitHub Pages)."""

import json
import re
import unicodedata
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from .config import (
    DOCS_DATA_FILE,
    DOCS_DIR,
    DEFAULT_JPY_PLN_RATE,
    DEFAULT_EUR_PLN_RATE,
    MAX_CAMERA_PRICE_PLN,
    MAX_LENS_PRICE_PLN,
    CATEGORY_SHIPPING_SHARES,
    DEFAULT_SHIPPING_SHARE_PLN,
    ZENMARKET_FEE_JPY,
    ZENMARKET_FEE_EUR,
    ZENMARKET_DEPOSIT_FEE_RATE,
    VAT_RATE
)
from .costs import calculate_landed_cost, calculate_max_sniper_bid
from .checks import is_camera_item, is_lens_item
from .lot_vision_inspector import LotVisionInspector
from .closure_predictor import AuctionClosurePredictor


def clean_polish_market_queries(deal: Dict[str, Any]) -> Tuple[str, str]:
    """
    Produces:
    1) clean_pl_query: optimized Polish search phrase for Allegro listings.
    2) clean_olx_slug: URL-safe, lowercase, hyphenated ASCII slug for OLX (e.g. 'ps-vita-slim').
    
    Guarantees:
    - Zero Japanese characters or kanji brackets (【...】).
    - Zero URL-breaking symbols (%26, &, +, #).
    - True Polish market keywords.
    """
    model = deal.get("model", "")
    title = deal.get("title", "")
    text = f"{model} {title}".lower()

    # 1. Games & Mystery Lots / Bundles (prioritized over single console model matches)
    if any(w in text for w in ["danshari", "mystery", "karton", "pakiet", "zestaw", "mix", "hurtowy", "まとめ売り", "断捨離", "実家整理", "引退品"]):
        if "pokemon" in text or "pokémon" in text or "stwork" in text:
            pl_q = "gry pokemon nintendo"
        elif "3ds" in text or "ds" in text:
            pl_q = "gry nintendo ds zestaw"
        elif "gba" in text or "game boy" in text or "gb" in text:
            pl_q = "gry game boy advance zestaw"
        elif "psp" in text or "umd" in text:
            pl_q = "gry psp zestaw"
        elif "ps2" in text or "ps1" in text or "playstation 2" in text or "playstation 1" in text:
            pl_q = "gry ps2 zestaw"
        elif "sfc" in text or "super famicom" in text:
            pl_q = "gry super famicom"
        else:
            pl_q = "gry retro zestaw mix"

    # 2. Cameras
    elif "mju" in text:
        pl_q = "Olympus Mju II"
    elif "pc35af" in text:
        pl_q = "Pentax PC35AF"
    elif "tw2d" in text:
        pl_q = "Nikon TW2D"
    elif "autoboy" in text or "prima" in text:
        pl_q = "Canon Autoboy"
    elif "big mini" in text:
        pl_q = "Konica Big Mini"
    elif "espio" in text:
        pl_q = "Pentax Espio"
    elif "riva" in text:
        pl_q = "Minolta Riva"
    elif "trip 35" in text:
        pl_q = "Olympus Trip 35"
    elif "myport" in text:
        pl_q = "Ricoh Myport Zoom"
    elif "cardia" in text:
        pl_q = "Fuji Cardia Mini"
    elif "af-10 twin" in text or "af 10 twin" in text:
        pl_q = "Olympus AF-10 Twin"
    elif "yashica" in text:
        pl_q = "Kyocera Yashica Zoomate"
    elif "pop efj" in text:
        pl_q = "Konica Pop EFJ"

    # 3. Handhelds & Consoles
    elif "pch-2000" in text or ("vita" in text and "slim" in text):
        pl_q = "PS Vita Slim"
    elif "pch-1000" in text or ("vita" in text and "oled" in text):
        pl_q = "PS Vita OLED"
    elif "psp-2000" in text or "psp 2000" in text:
        pl_q = "Sony PSP 2000"
    elif "psp-3000" in text or "psp 3000" in text:
        pl_q = "Sony PSP 3000"
    elif "psp-1000" in text or "psp 1000" in text:
        pl_q = "Sony PSP 1000"
    elif "new" in text and "3ds" in text and ("ll" in text or "xl" in text):
        pl_q = "New Nintendo 3DS XL"
    elif "new" in text and "3ds" in text:
        pl_q = "New Nintendo 3DS"
    elif "3ds" in text and ("ll" in text or "xl" in text):
        pl_q = "Nintendo 3DS XL"
    elif "3ds" in text:
        pl_q = "Nintendo 3DS"
    elif "2ds" in text and ("ll" in text or "xl" in text):
        pl_q = "New Nintendo 2DS XL"
    elif "2ds" in text:
        pl_q = "Nintendo 2DS"
    elif "dsi ll" in text or "dsi xl" in text:
        pl_q = "Nintendo DSi XL"
    elif "dsi" in text:
        pl_q = "Nintendo DSi"
    elif "ds lite" in text:
        pl_q = "Nintendo DS Lite"
    elif "ags-101" in text:
        pl_q = "Game Boy Advance SP AGS-101"
    elif "famicom 20th" in text or ("famicom" in text and "sp" in text):
        pl_q = "Game Boy Advance SP Famicom"
    elif "torchic" in text:
        pl_q = "Game Boy Advance SP Torchic"
    elif "advance sp" in text or "gba sp" in text:
        pl_q = "Game Boy Advance SP"
    elif "game boy color" in text or "cgb-001" in text or "gbc" in text:
        pl_q = "Game Boy Color Pokemon" if ("pokemon" in text or "pokémon" in text) else "Game Boy Color"
    elif "game boy micro" in text or "oxy-001" in text or "micro" in text:
        pl_q = "Game Boy Micro"
    elif "agb-001" in text or "advance" in text:
        pl_q = "Game Boy Advance"
    elif "psone combo" in text or "scph-130" in text:
        pl_q = "PSone LCD Combo SCPH-130"
    elif "gamecube" in text and "spice" in text:
        pl_q = "GameCube Spice Orange"
    elif "gamecube" in text:
        pl_q = "Nintendo GameCube"
    elif "ps4 pro" in text and "monster hunter" in text:
        pl_q = "PS4 Pro Monster Hunter"
    elif "ps4" in text and "metal gear" in text:
        pl_q = "PS4 Metal Gear Solid V"

    # 4. Controllers
    elif "astro bot" in text:
        pl_q = "DualSense Astro Bot"
    elif "monster hunter" in text and "dualsense" in text:
        pl_q = "DualSense Monster Hunter"
    elif "god of war" in text and "dualsense" in text:
        pl_q = "DualSense God of War"
    elif "final fantasy" in text and "dualsense" in text:
        pl_q = "DualSense Final Fantasy XVI"
    elif "spider-man" in text and "dualsense" in text:
        pl_q = "DualSense Spider-Man 2"
    elif "30th" in text and "dualsense" in text:
        pl_q = "DualSense 30th Anniversary"
    elif "slime" in text:
        pl_q = "Dragon Quest Slime PS2"
    elif "rathalos" in text or ("monster hunter" in text and "dualshock" in text):
        pl_q = "DualShock 4 Monster Hunter"
    elif "berry blue" in text:
        pl_q = "DualShock 4 Berry Blue"
    elif "500 million" in text:
        pl_q = "DualShock 4 500 Million"
    elif "death stranding" in text:
        pl_q = "DualShock 4 Death Stranding"
    elif "metallic blue" in text:
        pl_q = "DualShock 3 Metallic Blue"
    elif "island blue" in text:
        pl_q = "DualShock Island Blue PS1"
    elif "emerald green" in text:
        pl_q = "DualShock 2 Emerald Green"
    elif "dualsense" in text:
        pl_q = "DualSense PS5"
    elif "dualshock 4" in text:
        pl_q = "DualShock 4"

    # 5. Lenses
    elif "super-takumar 55mm" in text or "takumar 55mm" in text:
        pl_q = "Super-Takumar 55mm 1.8"
    elif "pentax-m 50mm" in text and "1.4" in text:
        pl_q = "Pentax-M 50mm 1.4"
    elif "pentax-m 50mm" in text:
        pl_q = "Pentax-M 50mm f2"
    elif "canon fd 50mm" in text:
        pl_q = "Canon FD 50mm 1.8"
    elif "minolta md 50mm" in text:
        pl_q = "Minolta MD 50mm 1.7"
    elif "zuiko 50mm" in text:
        pl_q = "Zuiko 50mm 1.8"
    elif "pentax 28mm" in text:
        pl_q = "Pentax 28mm 2.8"

    else:
        # Generic clean
        t = re.sub(r"[\u3000-\u303f\u3040-\u309f\u30a0-\u30ff\uff00-\uffef\u4e00-\u9faf]", "", model or title)
        t = re.sub(r"【.*?】", "", t)
        t = re.sub(r"\(.*?\)", "", t)
        t = t.replace("&", " i ").replace("/", " ")
        t = re.sub(r"[^a-zA-Z0-9\sąćęłńóśźżĄĆĘŁŃÓŚŹŻ-]", " ", t)
        words = t.split()[:4]
        pl_q = " ".join(words) if words else "retro gry"

    slug_base = unicodedata.normalize("NFKD", pl_q).encode("ascii", "ignore").decode("utf-8").lower()
    clean_olx_slug = re.sub(r"[^a-z0-9]+", "-", slug_base).strip("-")
    if not clean_olx_slug:
        clean_olx_slug = "retro-gry"
    return pl_q, clean_olx_slug


class WebappExporter:
    """Exports unified deals, auctions, rates, and analytics for the Android / GitHub Pages Web App."""

    def __init__(
        self,
        rate_jpy: float = DEFAULT_JPY_PLN_RATE,
        rate_eur: float = DEFAULT_EUR_PLN_RATE,
        is_live_rate: bool = False,
        timeline_status: Optional[Dict[str, Any]] = None,
        mercari_deals: Optional[List[Dict[str, Any]]] = None,
        yahoo_deals: Optional[List[Dict[str, Any]]] = None,
        history_stats: Optional[Dict[str, Any]] = None,
    ):
        self.rate_jpy = float(rate_jpy)
        self.rate_eur = float(rate_eur)
        self.is_live_rate = is_live_rate
        self.timeline = timeline_status or {
            "days_remaining": 58,
            "deadline": "2027-01-06",
            "start_date": "2026-11-07"
        }
        self.raw_mercari = mercari_deals or []
        self.raw_yahoo = yahoo_deals or []
        self.history_stats = history_stats or {
            "total_sales": 49,
            "realized_profit": 11447.37,
            "avg_roi": 82.8
        }

    def process_yahoo_deal(self, deal: Dict[str, Any]) -> Dict[str, Any]:
        """Processes and standardizes a Yahoo Auction deal item."""
        d = dict(deal)
        cat_id = d.get("category_id", "other")
        est_pl = float(d.get("est_pl_value", 0))
        price_jpy = float(d.get("price_jpy", 0))
        query = d.get("search_query_jp", d.get("model", ""))
        encoded_q = urllib.parse.quote(query)

        # Landed cost at current price
        cost_info = calculate_landed_cost(
            price_jpy=price_jpy,
            category_id=cat_id,
            rate_jpy=self.rate_jpy,
            rate_eur=self.rate_eur
        )
        landed_cost = cost_info["landed_cost_pln"]
        est_margin = round(est_pl - landed_cost, 2)
        roi_pct = round((est_margin / landed_cost * 100.0), 1) if landed_cost > 0 else 0.0

        # Target ROI hurdle
        if "games_mix" in cat_id or est_pl <= 500:
            target_roi = 40.0
        elif est_pl >= 1200:
            target_roi = 28.0
        else:
            target_roi = 32.0

        cap_info = calculate_max_sniper_bid(
            est_pl_value=est_pl,
            category_id=cat_id,
            target_roi_pct=target_roi,
            rate_jpy=self.rate_jpy,
            rate_eur=self.rate_eur
        )
        max_bid = cap_info["max_bid_jpy"]
        guar_margin = cap_info["guaranteed_margin_pln"]
        guar_roi = cap_info["guaranteed_roi_pct"]

        # Strict caps on cameras and lenses
        if is_camera_item(d) or cat_id == "film_cameras_point_shoot":
            max_cam = int((MAX_CAMERA_PRICE_PLN / self.rate_jpy) // 100 * 100)
            if max_bid > max_cam:
                max_bid = max_cam
                rc = calculate_landed_cost(max_bid, cat_id, self.rate_jpy, self.rate_eur)
                guar_margin = round(est_pl - rc["landed_cost_pln"], 2)
                guar_roi = round((guar_margin / rc["landed_cost_pln"] * 100.0), 1) if rc["landed_cost_pln"] > 0 else 0.0

        if is_lens_item(d) or cat_id == "analog_lenses":
            max_lens = int((MAX_LENS_PRICE_PLN / self.rate_jpy) // 100 * 100)
            if max_bid > max_lens:
                max_bid = max_lens
                rc = calculate_landed_cost(max_bid, cat_id, self.rate_jpy, self.rate_eur)
                guar_margin = round(est_pl - rc["landed_cost_pln"], 2)
                guar_roi = round((guar_margin / rc["landed_cost_pln"] * 100.0), 1) if rc["landed_cost_pln"] > 0 else 0.0

        c_min = d.get("closed_price_min_jpy", int(price_jpy * 0.85))
        c_max = d.get("closed_price_max_jpy", int(price_jpy * 1.15))
        c_avg = d.get("closed_price_avg_jpy", int(price_jpy))
        mercari_avg = d.get("mercari_bin_avg_jpy", int(c_avg * 1.3))

        diff_jpy = mercari_avg - c_avg
        diff_pct = round((diff_jpy / mercari_avg * 100.0), 1) if mercari_avg > 0 else 0.0

        b_type = d.get("battery_type", "none")
        has_battery = (b_type == "li-ion")

        # Resolve image URL
        image_url = self._resolve_image_url(d, cat_id)

        # Allegro completed archive & OLX clean query
        clean_pl_q, clean_olx_slug = clean_polish_market_queries(d)
        allegro_url = f"https://allegro.pl/listing?string={urllib.parse.quote(clean_pl_q)}"
        olx_url = f"https://www.olx.pl/oferty/q-{clean_olx_slug}/"
        allegro_pln = float(d.get("allegro_archive_pln", round(est_pl * 1.08, 1)))
        olx_pln = float(d.get("olx_haggled_pln", round(est_pl * 0.90, 1)))

        time_rem = d.get("time_remaining_minutes")
        if time_rem is None:
            time_rem = 120
        time_formatted = d.get("time_remaining_formatted") or (f"{time_rem} min" if time_rem < 60 else f"{time_rem // 60}h")
        ends_at = d.get("ends_at", "")
        price_stage_note = d.get("price_stage_note", "")
        if not price_stage_note:
            if time_rem <= 60:
                price_stage_note = "🔥 Faza Końcowa (<60m) – Prawdziwa cena rynkowa (落札相場)!"
            elif time_rem <= 360:
                price_stage_note = "⚡ Ostatnie godziny (1-6h) – Walka snajperów w toku"
            elif time_rem <= 1440:
                price_stage_note = "⏳ Średnia faza (6-24h) – Oferty wzrosną pod koniec"
            else:
                price_stage_note = "🕒 Wczesna faza (1-2 dni) – Startowa oferta, wzrośnie pod koniec"
        is_ending_soon = bool(d.get("is_ending_soon", time_rem <= 120))

        # Closure price prediction & condition grading (落札相場)
        pred = AuctionClosurePredictor.predict_closure(d, self.rate_jpy, self.rate_eur)

        return {
            "id": d.get("id"),
            "platform": d.get("platform", "Yahoo! Auctions Japan"),
            "category_id": cat_id,
            "category_name": d.get("category_name", ""),
            "model": d.get("model", ""),
            "color": d.get("color", ""),
            "battery_type": b_type,
            "has_battery": has_battery,
            "image_url": image_url,
            "status": d.get("status", "Aktywna Aukcja"),
            "condition_badge": d.get("condition_badge", "✅ Sprawdzony"),
            "custom_note": d.get("custom_note", ""),
            "time_remaining_minutes": time_rem,
            "time_remaining_formatted": time_formatted,
            "ends_at": ends_at,
            "price_stage_note": price_stage_note,
            "is_ending_soon": is_ending_soon,
            "predicted_closure_jpy": pred["predicted_closure_jpy"],
            "predicted_closure_min_jpy": pred["predicted_closure_min_jpy"],
            "predicted_closure_max_jpy": pred["predicted_closure_max_jpy"],
            "predicted_closure_pln": pred["predicted_closure_pln"],
            "closure_gap_jpy": pred["closure_gap_jpy"],
            "closure_gap_pct": pred["closure_gap_pct"],
            "expected_landed_cost_pln": pred["expected_landed_cost_pln"],
            "expected_margin_pln": pred["expected_margin_pln"],
            "expected_roi_pct": pred["expected_roi_pct"],
            "condition_grade": pred["condition_grade"],
            "condition_label": pred["condition_label"],
            "condition_short_label": pred["condition_short_label"],
            "condition_badge_color": pred["condition_badge_color"],
            "condition_features": pred["condition_features"],
            "condition_desc": pred["condition_desc"],
            "verdict_code": pred["verdict_code"],
            "verdict_label": pred["verdict_label"],
            "verdict_badge_class": pred["verdict_badge_class"],
            "recommendation_text": pred["recommendation_text"],
            "price_jpy": price_jpy,
            "price_pln_raw": cost_info["price_pln_raw"],
            "landed_cost_pln": landed_cost,
            "est_pl_value": est_pl,
            "allegro_archive_pln": allegro_pln,
            "olx_haggled_pln": olx_pln,
            "est_margin_pln": est_margin,
            "roi_percent": roi_pct,
            "max_bid_jpy": max_bid,
            "guaranteed_margin_pln": guar_margin,
            "guaranteed_roi_pct": guar_roi,
            "closed_price_min_jpy": c_min,
            "closed_price_max_jpy": c_max,
            "closed_price_avg_jpy": c_avg,
            "mercari_bin_avg_jpy": mercari_avg,
            "arbitrage_discount_pct": diff_pct,
            "auction_advantage_note": d.get("auction_advantage_note", ""),
            "shipping_share_pln": cost_info["shipping_share_pln"],
            "vat_pln": cost_info["vat_pln"],
            "zenmarket_fee_pln": cost_info["zenmarket_fee_pln"],
            "photo_inspection": d.get("photo_inspection") or (
                LotVisionInspector.inspect_lot_photo_contents(d)
                if ("danshari" in cat_id or "mystery" in cat_id or "retro_games" in cat_id or LotVisionInspector.detect_danshari_type(" ".join([d.get("model", ""), d.get("search_query_jp", "")]))["is_mystery_lot"])
                else None
            ),
            "links": {
                "zenmarket_sniper": d.get("zenmarket_url", f"https://zenmarket.jp/pl/yahoo.aspx?q={encoded_q}"),
                "zenmarket_ending_soon": f"https://zenmarket.jp/pl/yahoo.aspx?q={encoded_q}&sort=end&order=asc",
                "zenmarket_lowest_bid": f"https://zenmarket.jp/pl/yahoo.aspx?q={encoded_q}&sort=price&order=asc",
                "zenmarket_mercari_stream": f"https://zenmarket.jp/pl/mercari.aspx?q={encoded_q}",
                "mercari_live_search": f"https://jp.mercari.com/search?keyword={encoded_q}&status=on_sale",
                "buyee_url": d.get("buyee_url", f"https://buyee.jp/item/search/query/{encoded_q}?translationType=1"),
                "yahoo_closed_archive": f"https://auctions.yahoo.co.jp/closedsearch/closedsearch?p={encoded_q}",
                "yahoo_direct": d.get("source_url", f"https://auctions.yahoo.co.jp/search/search?p={encoded_q}"),
                "allegro_search": allegro_url,
                "olx_search": olx_url
            }
        }

    def _resolve_image_url(self, deal: Dict[str, Any], cat_id: str) -> str:
        """Resolves a high-quality product image URL or returns an optimized vector SVG asset."""
        img = deal.get("image_url")
        if img and isinstance(img, str) and img.strip() and img != "None":
            return img.strip()

        cid = (cat_id or "").lower()
        mod = (deal.get("model", "") or deal.get("title", "") or "").lower()

        if "danshari" in cid or "mystery" in cid or "rozno" in cid or "断捨離" in mod or "処分" in mod or "雑多" in mod or "福袋" in mod:
            return "./assets/images/mystery_lot.svg"
        elif "vita" in cid or "vita" in mod:
            return "./assets/images/ps_vita.svg"
        elif "psp" in cid or "psp" in mod:
            return "./assets/images/psp.svg"
        elif "3ds" in cid or "3ds" in mod or "2ds" in mod:
            return "./assets/images/n3ds_xl.svg"
        elif "ds" in cid or "dsi" in mod or "ds lite" in mod:
            return "./assets/images/ds_lite.svg"
        elif "gameboy" in cid or "gba" in mod or "gbc" in mod or "micro" in mod:
            return "./assets/images/gba_sp.svg"
        elif "camera" in cid or "film" in cid or "aparat" in mod or "autoboy" in mod or "espio" in mod or "riva" in mod or "trip" in mod or "mju" in mod or "pc35af" in mod:
            return "./assets/images/camera_point_shoot.svg"
        elif "lens" in cid or "obiektyw" in mod or "takumar" in mod or "pentax-m" in mod or "zuiko" in mod or "chinon" in mod:
            return "./assets/images/analog_lens.svg"
        elif "controller" in cid or "pad" in mod or "dualsense" in mod or "dualshock" in mod or "slime" in mod:
            return "./assets/images/controller.svg"
        elif "games_mix" in cid or "gry" in mod or "mix" in mod or "soft" in mod:
            return "./assets/images/retro_games.svg"
        elif "curated" in cid or "console" in cid or "ps4" in mod or "psone" in mod or "gamecube" in mod or "dreamcast" in mod or "ps2" in mod:
            return "./assets/images/curated_console.svg"

        return "./assets/images/placeholder.svg"

    def process_mercari_deal(self, deal: Dict[str, Any]) -> Dict[str, Any]:
        """Processes and standardizes an active Mercari deal item."""
        d = dict(deal)
        cat_id = d.get("category_id", "other")
        b_type = d.get("battery_type", "none")
        has_battery = (b_type == "li-ion")
        est_pl = float(d.get("est_pl_value", 0.0))

        image_url = self._resolve_image_url(d, cat_id)
        clean_pl_q, clean_olx_slug = clean_polish_market_queries(d)
        allegro_url = f"https://allegro.pl/listing?string={urllib.parse.quote(clean_pl_q)}"
        olx_url = f"https://www.olx.pl/oferty/q-{clean_olx_slug}/"
        allegro_pln = float(d.get("allegro_archive_pln", round(est_pl * 1.08, 1)))
        olx_pln = float(d.get("olx_haggled_pln", round(est_pl * 0.90, 1)))

        query_jp = d.get("search_query_jp") or d.get("model", "")
        encoded_q = urllib.parse.quote(query_jp)

        # Resolve buy and direct links without internal proxy ID leak
        iid = str(d.get("id", ""))
        is_real_mercari = bool(re.match(r"^m\d+$", iid))
        
        zen_buy = d.get("zenmarket_url")
        if not zen_buy or "danshari_" in zen_buy or "pentax_pc35af_manual" in zen_buy or "mju_2_prime_black" in zen_buy:
            if is_real_mercari:
                zen_buy = f"https://zenmarket.jp/pl/mercariproduct.aspx?itemCode={iid}"
            else:
                zen_buy = f"https://zenmarket.jp/pl/yahoo.aspx?q={encoded_q}"

        merc_direct = d.get("mercari_url")
        if not merc_direct or not is_real_mercari:
            merc_direct = f"https://jp.mercari.com/search?keyword={encoded_q}&status=on_sale" if not is_real_mercari else f"https://jp.mercari.com/item/{iid}"

        return {
            "id": d.get("id"),
            "platform": "Mercari Japan",
            "category_id": cat_id,
            "category_name": d.get("category_name", ""),
            "model": d.get("model", d.get("title", "")),
            "color": d.get("color", ""),
            "battery_type": b_type,
            "has_battery": has_battery,
            "image_url": image_url,
            "status": d.get("status", "Dostępne"),
            "condition_badge": d.get("condition_badge", "✅ Stan Dobry"),
            "custom_note": d.get("custom_note", d.get("title", "")),
            "time_remaining_minutes": 0,
            "time_remaining_formatted": "Kup Teraz (Stała cena)",
            "ends_at": "Natychmiastowy zakup (Kup Teraz)",
            "price_stage_note": "✅ Cena stała (Kup Teraz) – Prawdziwa cena bez licytacji",
            "is_ending_soon": False,
            "predicted_closure_jpy": d.get("price_jpy", 0),
            "predicted_closure_min_jpy": d.get("price_jpy", 0),
            "predicted_closure_max_jpy": d.get("price_jpy", 0),
            "predicted_closure_pln": d.get("price_pln_raw", 0.0),
            "closure_gap_jpy": 0,
            "closure_gap_pct": 0.0,
            "expected_landed_cost_pln": d.get("landed_cost_pln", 0.0),
            "expected_margin_pln": d.get("est_margin_pln", 0.0),
            "expected_roi_pct": d.get("roi_percent", 0.0),
            "condition_grade": "MERCARI_BIN",
            "condition_label": "🛍️ Kup Teraz (Cena Stała)",
            "condition_short_label": "Kup Teraz",
            "condition_badge_color": "#10b981",
            "condition_features": ["Natychmiastowy zakup", "Gwarancja stałej ceny"],
            "condition_desc": "Przedmiot z ceną Kup Teraz – brak licytacji, cena ostateczna",
            "verdict_code": "MERCARI_INSTANT_BUY",
            "verdict_label": "🛍️ KUP TERAZ: STAŁA CENA",
            "verdict_badge_class": "verdict-mercari",
            "recommendation_text": "Cena ostateczna. Kupuj bez ryzyka podbicia ceny przez snajperów.",
            "price_jpy": d.get("price_jpy", 0),
            "price_pln_raw": d.get("price_pln_raw", 0.0),
            "landed_cost_pln": d.get("landed_cost_pln", 0.0),
            "est_pl_value": est_pl,
            "allegro_archive_pln": allegro_pln,
            "olx_haggled_pln": olx_pln,
            "est_margin_pln": d.get("est_margin_pln", 0.0),
            "roi_percent": d.get("roi_percent", 0.0),
            "shipping_share_pln": d.get("shipping_share_pln", 30.0),
            "vat_pln": d.get("vat_pln", 0.0),
            "zenmarket_fee_pln": d.get("zenmarket_fee_pln", 0.0),
            "photo_inspection": d.get("photo_inspection") or (
                LotVisionInspector.inspect_lot_photo_contents(d)
                if ("danshari" in cat_id or "mystery" in cat_id or "retro_games" in cat_id or LotVisionInspector.detect_danshari_type(" ".join([d.get("model", ""), d.get("custom_note", "")]))["is_mystery_lot"])
                else None
            ),
            "links": {
                "zenmarket_buy": zen_buy,
                "mercari_direct": merc_direct,
                "zenmarket_search_mercari": f"https://zenmarket.jp/pl/mercari.aspx?q={encoded_q}",
                "mercari_live_search": f"https://jp.mercari.com/search?keyword={encoded_q}&status=on_sale",
                "zenmarket_yahoo_search": f"https://zenmarket.jp/pl/yahoo.aspx?q={encoded_q}",
                "allegro_search": allegro_url,
                "olx_search": olx_url
            }
        }

    def export(self, output_file: Optional[Path] = None) -> Dict[str, Any]:
        """Compiles and writes docs/data/deals.json."""
        target_path = output_file or DOCS_DATA_FILE
        target_path.parent.mkdir(parents=True, exist_ok=True)

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M UTC")

        # Process Yahoo Auctions
        processed_auctions = [self.process_yahoo_deal(d) for d in self.raw_yahoo]

        # Sort Yahoo Auctions by remaining time ascending by default (ending soonest first – true prices)
        processed_auctions.sort(
            key=lambda x: (
                x.get("time_remaining_minutes") if x.get("time_remaining_minutes") is not None else 999999,
                -x.get("est_margin_pln", 0)
            )
        )

        # Process Mercari Deals (only active / available)
        active_mercari = [
            self.process_mercari_deal(d) for d in self.raw_mercari
            if "Dostępne" in str(d.get("status", ""))
        ]

        # Categories catalogue with metadata
        categories = [
            {"id": "all", "name": "Wszystkie Okazje", "icon": "🌐", "count": len(processed_auctions) + len(active_mercari)},
            {"id": "nintendo_3ds_handhelds", "name": "Nintendo 3DS & New 3DS", "icon": "🕹️", "battery": True},
            {"id": "nintendo_ds_handhelds", "name": "Nintendo DSi LL & DS Lite", "icon": "🎮", "battery": True},
            {"id": "gameboy_advance_retro", "name": "Game Boy Advance & Retro", "icon": "👾", "battery": True},
            {"id": "ps_vita", "name": "PlayStation Vita (Slim/OLED)", "icon": "✨", "battery": True},
            {"id": "psp_handheld", "name": "Sony PSP Handhelds", "icon": "⚡", "battery": True},
            {"id": "retro_games_mix", "name": "Pakiety Gier Retro (0% Baterii)", "icon": "📦", "battery": False},
            {"id": "danshari_mystery_lots", "name": "Pakiety Różności (Danshari / Skarby)", "icon": "🎁", "battery": False},
            {"id": "high_margin_curated_consoles", "name": "Wyselekcjonowane Stacjonarne", "icon": "💎", "battery": False},
            {"id": "ps5_limited_controllers", "name": "Kontrolery Limitowane PS5", "icon": "🎮", "battery": True},
            {"id": "ps_retro_limited_controllers", "name": "Kontrolery Retro PS1-PS4", "icon": "🎯", "battery": False},
            {"id": "film_cameras_point_shoot", "name": "Aparaty Kompaktowe 35mm (<= 100 zł)", "icon": "📷", "battery": False},
            {"id": "analog_lenses", "name": "Japońskie Obiektywy Manualne (<= 100 zł)", "icon": "🔍", "battery": False}
        ]

        data = {
            "meta": {
                "generated_at": now_str,
                "app_title": "AgyDeal – Japan Deal & Auction Sniping Radar",
                "app_version": "2.0.0",
                "exchange_rates": {
                    "rate_jpy": self.rate_jpy,
                    "rate_eur": self.rate_eur,
                    "is_live": self.is_live_rate,
                    "jpy_100_pln": round(self.rate_jpy * 100, 2),
                    "eur_1_pln": round(self.rate_eur, 4)
                },
                "zenmarket_fees": {
                    "domestic_jpy": ZENMARKET_FEE_JPY,
                    "handling_eur": ZENMARKET_FEE_EUR,
                    "deposit_rate": ZENMARKET_DEPOSIT_FEE_RATE,
                    "vat_rate": VAT_RATE
                },
                "storage_window": {
                    "days_remaining": self.timeline.get("days_remaining", 58),
                    "deadline": self.timeline.get("deadline", "2027-01-06"),
                    "start_date": self.timeline.get("start_date", "2026-11-07")
                },
                "sales_history_summary": self.history_stats,
                "counts": {
                    "yahoo_auctions": len(processed_auctions),
                    "mercari_deals": len(active_mercari),
                    "total_active": len(processed_auctions) + len(active_mercari)
                }
            },
            "categories": categories,
            "auctions": processed_auctions,
            "mercari_deals": active_mercari
        }

        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"📱 Webapp Exporter: Saved {len(processed_auctions)} auctions and {len(active_mercari)} Mercari deals to {target_path}")
        return {
            "target_path": str(target_path),
            "auctions_count": len(processed_auctions),
            "mercari_count": len(active_mercari)
        }
