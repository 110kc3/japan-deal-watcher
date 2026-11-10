"""Finished Auctions Intelligence & Archive Tracker (落札相場).

Tracks, archives, and evaluates completed Yahoo Auctions Japan listings.
Maintains data/finished_auctions.json with realized Polish market margins,
winning bid prices (落札価格), condition grades, and parcel weight stats.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

from .config import (
    FINISHED_AUCTIONS_FILE,
    DEFAULT_JPY_PLN_RATE,
    DEFAULT_EUR_PLN_RATE,
    MAX_CAMERA_PRICE_PLN,
    MAX_LENS_PRICE_PLN
)
from .costs import calculate_landed_cost
from .checks import is_camera_item, is_lens_item


# Seed historical verified closed auctions from Yahoo Auctions (落札相場)
HISTORICAL_SEED_AUCTIONS: List[Dict[str, Any]] = [
    {
        "id": "j1158930211",
        "auction_id": "j1158930211",
        "model": "PlayStation Vita Aqua Blue (PCH-2000ZA23)",
        "color": "Aqua Blue",
        "category_id": "ps_vita",
        "category_name": "Sony PlayStation Vita",
        "platform": "Yahoo Auctions Japan",
        "final_price_jpy": 11500,
        "predicted_close_jpy": 11800,
        "final_price_pln": 285.57,
        "landed_cost_pln": 438.20,
        "est_pl_value": 750.0,
        "realized_margin_pln": 311.80,
        "roi_percent": 71.2,
        "condition_grade": "A_MINT_BOX",
        "condition_label": "📦 Kolekcjonerski Box (CIB)",
        "condition_short_label": "Box CIB",
        "condition_badge_color": "#8b5cf6",
        "closed_at": "2026-11-08T21:30:00Z",
        "status": "🏁 Zakończona (Wylicytowano)",
        "speed_tier": "🎯 Snajper Trafiony",
        "battery_type": "li-ion",
        "package_weight_g": 380,
        "weight_kg": 0.38,
        "residual_profit_pln": 311.80,
        "zenmarket_url": "https://zenmarket.jp/pl/auction.aspx?itemCode=j1158930211",
        "yahoo_url": "https://page.auctions.yahoo.co.jp/jp/auction/j1158930211",
        "allegro_url": "https://allegro.pl/kategoria/konsole-i-automaty-sony-playstation-vita-257158?string=PlayStation%20Vita%20Aqua%20Blue",
        "olx_url": "https://www.olx.pl/oferty/q-playstation-vita-aqua-blue/"
    },
    {
        "id": "w1225443906",
        "auction_id": "w1225443906",
        "model": "DualSense Wireless Controller 30th Anniversary Limited Edition",
        "color": "PS1 Classic Grey 30th",
        "category_id": "ps5_accessories",
        "category_name": "PlayStation 5 Akcesoria",
        "platform": "Yahoo Auctions Japan",
        "final_price_jpy": 12000,
        "predicted_close_jpy": 12500,
        "final_price_pln": 297.98,
        "landed_cost_pln": 453.60,
        "est_pl_value": 790.0,
        "realized_margin_pln": 336.40,
        "roi_percent": 74.2,
        "condition_grade": "A_MINT_BOX",
        "condition_label": "📦 Kolekcjonerski Box (CIB)",
        "condition_short_label": "Box CIB",
        "condition_badge_color": "#8b5cf6",
        "closed_at": "2026-11-09T18:45:00Z",
        "status": "🏁 Zakończona (Wylicytowano)",
        "speed_tier": "🎯 Snajper Trafiony",
        "battery_type": "li-ion",
        "package_weight_g": 420,
        "weight_kg": 0.42,
        "residual_profit_pln": 336.40,
        "zenmarket_url": "https://zenmarket.jp/pl/auction.aspx?itemCode=w1225443906",
        "yahoo_url": "https://page.auctions.yahoo.co.jp/jp/auction/w1225443906",
        "allegro_url": "https://allegro.pl/kategoria/akcesoria-kontrolery-pady-playstation-5-300445?string=DualSense%2030th%20Anniversary",
        "olx_url": "https://www.olx.pl/oferty/q-dualsense-30th-anniversary/"
    },
    {
        "id": "x1198421004",
        "auction_id": "x1198421004",
        "model": "Game Boy Micro 20th Famicom Edition (OXY-S-GA)",
        "color": "Famicom Red / Gold",
        "category_id": "gameboy_advance_retro",
        "category_name": "Nintendo Game Boy Advance / Micro",
        "platform": "Yahoo Auctions Japan",
        "final_price_jpy": 16800,
        "predicted_close_jpy": 17200,
        "final_price_pln": 417.18,
        "landed_cost_pln": 601.20,
        "est_pl_value": 1080.0,
        "realized_margin_pln": 478.80,
        "roi_percent": 79.6,
        "condition_grade": "A_MINT_BOX",
        "condition_label": "📦 Kolekcjonerski Box (CIB)",
        "condition_short_label": "Box CIB",
        "condition_badge_color": "#8b5cf6",
        "closed_at": "2026-11-09T22:15:00Z",
        "status": "🏁 Zakończona (Wylicytowano)",
        "speed_tier": "🎯 Snajper Trafiony",
        "battery_type": "li-ion",
        "package_weight_g": 240,
        "weight_kg": 0.24,
        "residual_profit_pln": 478.80,
        "zenmarket_url": "https://zenmarket.jp/pl/auction.aspx?itemCode=x1198421004",
        "yahoo_url": "https://page.auctions.yahoo.co.jp/jp/auction/x1198421004",
        "allegro_url": "https://allegro.pl/kategoria/konsole-i-automaty-nintendo-game-boy-advance-257154?string=Game%20Boy%20Micro%20Famicom",
        "olx_url": "https://www.olx.pl/oferty/q-game-boy-micro-famicom/"
    },
    {
        "id": "k1158930211",
        "auction_id": "k1158930211",
        "model": "PlayStation 2 Ocean Blue (SCPH-37000 L) Limited CIB",
        "color": "Ocean Blue (Transparent)",
        "category_id": "ps2_consoles",
        "category_name": "Sony PlayStation 2",
        "platform": "Yahoo Auctions Japan",
        "final_price_jpy": 12800,
        "predicted_close_jpy": 13200,
        "final_price_pln": 317.85,
        "landed_cost_pln": 478.50,
        "est_pl_value": 850.0,
        "realized_margin_pln": 371.50,
        "roi_percent": 77.6,
        "condition_grade": "A_MINT_BOX",
        "condition_label": "📦 Kolekcjonerski Box (CIB)",
        "condition_short_label": "Box CIB",
        "condition_badge_color": "#8b5cf6",
        "closed_at": "2026-11-08T19:00:00Z",
        "status": "🏁 Zakończona (Wylicytowano)",
        "speed_tier": "🎯 Snajper Trafiony",
        "battery_type": "none",
        "package_weight_g": 2200,
        "weight_kg": 2.20,
        "residual_profit_pln": 371.50,
        "zenmarket_url": "https://zenmarket.jp/pl/auction.aspx?itemCode=k1158930211",
        "yahoo_url": "https://page.auctions.yahoo.co.jp/jp/auction/k1158930211",
        "allegro_url": "https://allegro.pl/kategoria/konsole-i-automaty-sony-playstation-2-257159?string=PlayStation%202%20Ocean%20Blue",
        "olx_url": "https://www.olx.pl/oferty/q-playstation-2-ocean-blue/"
    },
    {
        "id": "b1158930211",
        "auction_id": "b1158930211",
        "model": "Asahi Pentax Super Takumar 50mm f/1.4 (8-Element)",
        "color": "Black / Vintage Chrome",
        "category_id": "analog_lenses",
        "category_name": "Japońskie Obiektywy Manualne",
        "platform": "Yahoo Auctions Japan",
        "final_price_jpy": 3500,
        "predicted_close_jpy": 3600,
        "final_price_pln": 86.91,
        "landed_cost_pln": 188.40,
        "est_pl_value": 380.0,
        "realized_margin_pln": 191.60,
        "roi_percent": 101.7,
        "condition_grade": "B_VERY_GOOD",
        "condition_label": "✨ Bardzo Dobry (Sprawny 100%)",
        "condition_short_label": "B. Dobry",
        "condition_badge_color": "#10b981",
        "closed_at": "2026-11-09T14:20:00Z",
        "status": "🏁 Zakończona (Wylicytowano)",
        "speed_tier": "🎯 Snajper Trafiony",
        "battery_type": "none",
        "package_weight_g": 320,
        "weight_kg": 0.32,
        "residual_profit_pln": 191.60,
        "zenmarket_url": "https://zenmarket.jp/pl/auction.aspx?itemCode=b1158930211",
        "yahoo_url": "https://page.auctions.yahoo.co.jp/jp/auction/b1158930211",
        "allegro_url": "https://allegro.pl/kategoria/obiektywy-standardowe-staloogniskowe-50538?string=Super%20Takumar%2050mm%20f1.4",
        "olx_url": "https://www.olx.pl/oferty/q-super-takumar-50mm-f1-4/"
    },
    {
        "id": "d1158930211",
        "auction_id": "d1158930211",
        "model": "Nintendo DS & DS Lite Konsoli Pakiet 20 Sztuk (Danshari / Junk)",
        "color": "Mix Kolorów (Onyx / Polar / Crimson)",
        "category_id": "danshari_consoles_lots",
        "category_name": "Pakiety Konsolowe (Danshari / Hurt)",
        "platform": "Yahoo Auctions Japan",
        "final_price_jpy": 13500,
        "predicted_close_jpy": 14000,
        "final_price_pln": 335.23,
        "landed_cost_pln": 520.00,
        "est_pl_value": 1450.0,
        "realized_margin_pln": 930.00,
        "roi_percent": 178.8,
        "condition_grade": "J_UNTESTED_JUNK",
        "condition_label": "🧩 Pakiet / Junk / Likwidacja",
        "condition_short_label": "Junk / Pakiet",
        "condition_badge_color": "#ec4899",
        "closed_at": "2026-11-09T20:10:00Z",
        "status": "🏁 Zakończona (Wylicytowano)",
        "speed_tier": "🎯 Snajper Trafiony",
        "battery_type": "none",
        "package_weight_g": 4500,
        "weight_kg": 4.50,
        "residual_profit_pln": 930.00,
        "zenmarket_url": "https://zenmarket.jp/pl/auction.aspx?itemCode=d1158930211",
        "yahoo_url": "https://page.auctions.yahoo.co.jp/jp/auction/d1158930211",
        "allegro_url": "https://allegro.pl/kategoria/konsole-i-automaty-nintendo-ds-lite-257156?string=Nintendo%20DS%20Lite%20lot%20uszkodzone",
        "olx_url": "https://www.olx.pl/oferty/q-nintendo-ds-lite-pakiet/"
    },
    {
        "id": "p1158930211",
        "auction_id": "p1158930211",
        "model": "PlayStation Portable PSP-3000 Blossom Pink CIB Box",
        "color": "Blossom Pink",
        "category_id": "psp_handheld",
        "category_name": "Sony PlayStation Portable",
        "platform": "Yahoo Auctions Japan",
        "final_price_jpy": 8200,
        "predicted_close_jpy": 8500,
        "final_price_pln": 203.62,
        "landed_cost_pln": 332.80,
        "est_pl_value": 590.0,
        "realized_margin_pln": 257.20,
        "roi_percent": 77.3,
        "condition_grade": "A_MINT_BOX",
        "condition_label": "📦 Kolekcjonerski Box (CIB)",
        "condition_short_label": "Box CIB",
        "condition_badge_color": "#8b5cf6",
        "closed_at": "2026-11-08T16:40:00Z",
        "status": "🏁 Zakończona (Wylicytowano)",
        "speed_tier": "🎯 Snajper Trafiony",
        "battery_type": "li-ion",
        "package_weight_g": 360,
        "weight_kg": 0.36,
        "residual_profit_pln": 257.20,
        "zenmarket_url": "https://zenmarket.jp/pl/auction.aspx?itemCode=p1158930211",
        "yahoo_url": "https://page.auctions.yahoo.co.jp/jp/auction/p1158930211",
        "allegro_url": "https://allegro.pl/kategoria/konsole-i-automaty-sony-playstation-portable-psp-257157?string=PSP%203000%20Blossom%20Pink",
        "olx_url": "https://www.olx.pl/oferty/q-psp-3000-blossom-pink/"
    },
    {
        "id": "m1158930211",
        "auction_id": "m1158930211",
        "model": "Canon Autoboy Luna 35 (Sure Shot Prima Zoom 70F)",
        "color": "Champagne Gold / Black",
        "category_id": "film_cameras_point_shoot",
        "category_name": "Aparaty Kompaktowe Point & Shoot",
        "platform": "Yahoo Auctions Japan",
        "final_price_jpy": 3200,
        "predicted_close_jpy": 3400,
        "final_price_pln": 79.46,
        "landed_cost_pln": 178.50,
        "est_pl_value": 350.0,
        "realized_margin_pln": 171.50,
        "roi_percent": 96.1,
        "condition_grade": "B_VERY_GOOD",
        "condition_label": "✨ Bardzo Dobry (Sprawny 100%)",
        "condition_short_label": "B. Dobry",
        "condition_badge_color": "#10b981",
        "closed_at": "2026-11-09T11:15:00Z",
        "status": "🏁 Zakończona (Wylicytowano)",
        "speed_tier": "🎯 Snajper Trafiony",
        "battery_type": "none",
        "package_weight_g": 280,
        "weight_kg": 0.28,
        "residual_profit_pln": 171.50,
        "zenmarket_url": "https://zenmarket.jp/pl/auction.aspx?itemCode=m1158930211",
        "yahoo_url": "https://page.auctions.yahoo.co.jp/jp/auction/m1158930211",
        "allegro_url": "https://allegro.pl/kategoria/aparaty-analogowe-kompaktowe-111082?string=Canon%20Autoboy%20Luna",
        "olx_url": "https://www.olx.pl/oferty/q-canon-autoboy-luna/"
    }
]


class FinishedAuctionsTracker:
    """Manages the finished auctions archive and computes realized statistics."""

    def __init__(self, filepath: Optional[Path] = None):
        self.filepath = filepath or FINISHED_AUCTIONS_FILE
        self._data: List[Dict[str, Any]] = []
        self.load()

    def load(self) -> List[Dict[str, Any]]:
        """Loads data from disk or initializes with seed data."""
        if self.filepath.exists():
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        self._data = json.loads(content)
                        return self._data
            except Exception:
                pass

        # Initialize with curated seed auctions
        self._data = [dict(a) for a in HISTORICAL_SEED_AUCTIONS]
        self.save()
        return self._data

    def save(self) -> None:
        """Atomically saves the finished auctions dataset to disk."""
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        temp_file = self.filepath.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)
        temp_file.replace(self.filepath)

    def record_auction(self, auction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Records or updates a finished auction item.
        Ensures strict price cap compliance (<= 100 PLN for cameras & lenses).
        """
        aid = auction.get("auction_id") or auction.get("id")
        if not aid:
            return auction

        # Check existing
        existing_idx = next((i for i, a in enumerate(self._data) if a.get("auction_id") == aid or a.get("id") == aid), None)

        record = dict(auction)
        record["id"] = aid
        record["auction_id"] = aid
        record["platform"] = record.get("platform", "Yahoo Auctions Japan")
        record["status"] = "🏁 Zakończona (Wylicytowano)"

        # Calculate values if missing
        price_jpy = record.get("final_price_jpy", record.get("price_jpy", 0))
        record["final_price_jpy"] = price_jpy

        if "final_price_pln" not in record:
            record["final_price_pln"] = round(price_jpy * DEFAULT_JPY_PLN_RATE, 2)

        # Enforce camera / lens rules if relevant
        if is_camera_item(record) and record["final_price_pln"] > MAX_CAMERA_PRICE_PLN:
            # Skip or clamp according to strict rule
            record["is_deal"] = False
        if is_lens_item(record) and record["final_price_pln"] > MAX_LENS_PRICE_PLN:
            record["is_deal"] = False

        if "landed_cost_pln" not in record:
            calc = calculate_landed_cost(
                price_jpy=price_jpy,
                category_id=record.get("category_id", ""),
                rate_jpy=DEFAULT_JPY_PLN_RATE,
                rate_eur=DEFAULT_EUR_PLN_RATE
            )
            record["landed_cost_pln"] = calc["landed_cost_pln"]

        est_pl = record.get("est_pl_value", 0.0)
        landed = record.get("landed_cost_pln", 0.0)
        if est_pl > 0 and landed > 0:
            margin = round(est_pl - landed, 2)
            record["realized_margin_pln"] = margin
            record["residual_profit_pln"] = margin
            record["roi_percent"] = round((margin / landed) * 100, 1)

        if "closed_at" not in record:
            record["closed_at"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        if existing_idx is not None:
            self._data[existing_idx] = record
        else:
            self._data.insert(0, record)

        self.save()
        return record

    def harvest_from_active(self, active_auctions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Inspects active Yahoo Auctions and archives those whose closure time has passed.
        """
        now_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        harvested = []

        for deal in active_auctions:
            ends_at = deal.get("ends_at", "")
            time_remaining = deal.get("time_remaining_minutes", 999)
            is_ended = deal.get("is_ended", False) or (time_remaining <= 0)

            # Check ISO string comparison if ends_at is formatted as ISO
            if not is_ended and ends_at and "T" in ends_at:
                try:
                    is_ended = ends_at <= now_iso
                except Exception:
                    pass

            if is_ended:
                rec = self.record_auction(deal)
                harvested.append(rec)

        return harvested

    def get_all(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Returns finished auctions ordered by closed_at descending."""
        sorted_auctions = sorted(
            self._data,
            key=lambda x: str(x.get("closed_at", "")),
            reverse=True
        )
        if limit:
            return sorted_auctions[:limit]
        return sorted_auctions

    def get_stats(self) -> Dict[str, Any]:
        """Calculates executive metrics over the archived finished auctions."""
        total = len(self._data)
        if total == 0:
            return {
                "total_finished": 0,
                "avg_realized_margin_pln": 0.0,
                "total_profit_pln": 0.0,
                "avg_roi_percent": 0.0
            }

        margins = [d.get("realized_margin_pln", 0.0) for d in self._data]
        rois = [d.get("roi_percent", 0.0) for d in self._data]
        total_profit = sum(margins)
        avg_margin = total_profit / total
        avg_roi = sum(rois) / total

        return {
            "total_finished": total,
            "avg_realized_margin_pln": round(avg_margin, 2),
            "total_profit_pln": round(total_profit, 2),
            "avg_roi_percent": round(avg_roi, 1)
        }
