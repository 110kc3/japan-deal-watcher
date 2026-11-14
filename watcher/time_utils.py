"""Time and schedule utilities for auction end time calculations and timezone localization."""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
import zoneinfo

TZ_WARSAW = zoneinfo.ZoneInfo("Europe/Warsaw")
TZ_TOKYO = zoneinfo.ZoneInfo("Asia/Tokyo")

def format_time_remaining(minutes: int) -> str:
    """Formats remaining minutes into human-readable Polish notation."""
    if minutes <= 0:
        return "Zakończona"
    if minutes < 60:
        return f"{minutes} min"
    hours = minutes // 60
    rem_m = minutes % 60
    if hours < 24:
        return f"{hours}h {rem_m:02d}m" if rem_m > 0 else f"{hours}h"
    days = hours // 24
    rem_h = hours % 24
    return f"{days}d {rem_h}h" if rem_h > 0 else f"{days}d"

def calculate_auction_timing(
    deal: Dict[str, Any],
    ref_time_utc: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Computes precise, synchronized auction timing attributes across UTC,
    Polish time (Europe/Warsaw, DST-aware), and Japanese time (Asia/Tokyo).

    Preserves source end times and ensures expired auctions remain expired
    without resurrecting into the future.
    """
    now_utc = ref_time_utc or datetime.now(timezone.utc)
    if now_utc.tzinfo is None:
        now_utc = now_utc.replace(tzinfo=timezone.utc)

    now_pl = now_utc.astimezone(TZ_WARSAW)

    raw_ends_at = deal.get("ends_at")
    raw_minutes = deal.get("time_remaining_minutes")

    target_end_dt: Optional[datetime] = None
    has_valid_ends_at = False

    if raw_ends_at and isinstance(raw_ends_at, str):
        clean_str = raw_ends_at.replace(" UTC", "").replace("Z", "").strip()
        for fmt in ["%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M"]:
            try:
                parsed = datetime.strptime(clean_str, fmt).replace(tzinfo=timezone.utc)
                target_end_dt = parsed
                has_valid_ends_at = True
                break
            except ValueError:
                continue

    if has_valid_ends_at and target_end_dt is not None:
        diff_seconds = (target_end_dt - now_utc).total_seconds()
        if diff_seconds <= 0:
            minutes_rem = 0
            is_ended = True
        else:
            minutes_rem = max(0, int(round(diff_seconds / 60.0)))
            is_ended = False
    elif raw_minutes is not None:
        try:
            m_val = int(raw_minutes)
        except (ValueError, TypeError):
            m_val = 0
        if m_val <= 0:
            minutes_rem = 0
            is_ended = True
            target_end_dt = now_utc - timedelta(minutes=1)
        else:
            minutes_rem = m_val
            is_ended = False
            target_end_dt = now_utc + timedelta(minutes=m_val)
    else:
        status_str = str(deal.get("status", "")).lower()
        if "aktywna" in status_str or "active" in status_str:
            minutes_rem = 120
            is_ended = False
            target_end_dt = now_utc + timedelta(minutes=120)
        else:
            minutes_rem = 0
            is_ended = True
            target_end_dt = now_utc

    ends_at_utc_str = target_end_dt.strftime("%Y-%m-%d %H:%M UTC")
    ends_at_iso = target_end_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    end_pl = target_end_dt.astimezone(TZ_WARSAW)
    end_jst = target_end_dt.astimezone(TZ_TOKYO)

    pl_clock = end_pl.strftime("%H:%M")
    jst_clock = end_jst.strftime("%H:%M")

    days_diff = (end_pl.date() - now_pl.date()).days
    if is_ended:
        day_label = "Zakończona"
    elif days_diff == 0:
        day_label = "Dziś"
    elif days_diff == 1:
        day_label = "Jutro"
    elif days_diff == 2:
        day_label = "Pojutrze"
    else:
        day_label = end_pl.strftime("%d.%m")

    if is_ended:
        ends_at_formatted = f"Aukcja zakończona o {pl_clock} (PL)"
        ends_at_pl_short = f"Zakończona ({pl_clock})"
    else:
        ends_at_formatted = f"{day_label} o {pl_clock} (PL) / {jst_clock} (JP)"
        ends_at_pl_short = f"{day_label} {pl_clock}"

    time_formatted = format_time_remaining(minutes_rem)

    if minutes_rem == 0:
        price_stage_note = "Aukcja zakończona (落札終了)"
        is_ending_soon = False
    elif minutes_rem <= 60:
        price_stage_note = "🔥 Faza Końcowa (<60m) – Prawdziwa cena rynkowa (落札相場)!"
        is_ending_soon = True
    elif minutes_rem <= 360:
        price_stage_note = "⚡ Ostatnie godziny (1-6h) – Walka snajperów w toku"
        is_ending_soon = (minutes_rem <= 120)
    elif minutes_rem <= 1440:
        price_stage_note = "⏳ Średnia faza (6-24h) – Oferty wzrosną pod koniec"
        is_ending_soon = False
    else:
        price_stage_note = "🕒 Wczesna faza (1-2 dni) – Startowa oferta, wzrośnie pod koniec"
        is_ending_soon = False

    return {
        "time_remaining_minutes": minutes_rem,
        "time_remaining_formatted": time_formatted,
        "ends_at": ends_at_utc_str,
        "ends_at_iso": ends_at_iso,
        "ends_at_pl": pl_clock,
        "ends_at_jst": jst_clock,
        "ends_at_formatted": ends_at_formatted,
        "ends_at_pl_short": ends_at_pl_short,
        "price_stage_note": deal.get("price_stage_note") or price_stage_note,
        "is_ending_soon": is_ending_soon,
        "is_ended": is_ended
    }
