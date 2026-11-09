"""Exporter module for compiling Web App JSON data feed (Android PWA on GitHub Pages)."""

import json
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

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

        return {
            "id": d.get("id"),
            "platform": d.get("platform", "Yahoo! Auctions Japan"),
            "category_id": cat_id,
            "category_name": d.get("category_name", ""),
            "model": d.get("model", ""),
            "color": d.get("color", ""),
            "battery_type": b_type,
            "has_battery": has_battery,
            "status": d.get("status", "Aktywna Aukcja"),
            "condition_badge": d.get("condition_badge", "✅ Sprawdzony"),
            "custom_note": d.get("custom_note", ""),
            "price_jpy": price_jpy,
            "price_pln_raw": cost_info["price_pln_raw"],
            "landed_cost_pln": landed_cost,
            "est_pl_value": est_pl,
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
            "links": {
                "zenmarket_ending_soon": f"https://zenmarket.jp/pl/yahoo.aspx?q={encoded_q}&sort=end&order=asc",
                "zenmarket_lowest_bid": f"https://zenmarket.jp/pl/yahoo.aspx?q={encoded_q}&sort=price&order=asc",
                "zenmarket_sniper": d.get("zenmarket_url", f"https://zenmarket.jp/pl/yahoo.aspx?q={encoded_q}"),
                "buyee_url": d.get("buyee_url", f"https://buyee.jp/item/search/query/{encoded_q}?translationType=1"),
                "yahoo_closed_archive": f"https://auctions.yahoo.co.jp/closedsearch/closedsearch?p={encoded_q}",
                "yahoo_direct": d.get("source_url", f"https://auctions.yahoo.co.jp/search/search?p={encoded_q}")
            }
        }

    def process_mercari_deal(self, deal: Dict[str, Any]) -> Dict[str, Any]:
        """Processes and standardizes an active Mercari deal item."""
        d = dict(deal)
        b_type = d.get("battery_type", "none")
        has_battery = (b_type == "li-ion")

        return {
            "id": d.get("id"),
            "platform": "Mercari Japan",
            "category_id": d.get("category_id", "other"),
            "category_name": d.get("category_name", ""),
            "model": d.get("model", d.get("title", "")),
            "color": d.get("color", ""),
            "battery_type": b_type,
            "has_battery": has_battery,
            "status": d.get("status", "Dostępne"),
            "condition_badge": d.get("condition_badge", "✅ Stan Dobry"),
            "custom_note": d.get("custom_note", d.get("title", "")),
            "price_jpy": d.get("price_jpy", 0),
            "price_pln_raw": d.get("price_pln_raw", 0.0),
            "landed_cost_pln": d.get("landed_cost_pln", 0.0),
            "est_pl_value": d.get("est_pl_value", 0.0),
            "est_margin_pln": d.get("est_margin_pln", 0.0),
            "roi_percent": d.get("roi_percent", 0.0),
            "shipping_share_pln": d.get("shipping_share_pln", 30.0),
            "vat_pln": d.get("vat_pln", 0.0),
            "zenmarket_fee_pln": d.get("zenmarket_fee_pln", 0.0),
            "links": {
                "zenmarket_buy": d.get("zenmarket_url", f"https://zenmarket.jp/pl/mercariproduct.aspx?itemCode={d.get('id')}"),
                "mercari_direct": d.get("mercari_url", f"https://jp.mercari.com/item/{d.get('id')}")
            }
        }

    def export(self, output_file: Optional[Path] = None) -> Dict[str, Any]:
        """Compiles and writes docs/data/deals.json."""
        target_path = output_file or DOCS_DATA_FILE
        target_path.parent.mkdir(parents=True, exist_ok=True)

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M UTC")

        # Process Yahoo Auctions
        processed_auctions = [self.process_yahoo_deal(d) for d in self.raw_yahoo]

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
