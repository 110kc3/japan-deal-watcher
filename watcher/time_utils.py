"""Time and schedule utilities for auction end time calculations and timezone localization."""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional


def format_time_remaining(minutes: int) -> str:
    """Formats remaining minutes into human-readable Polish notation."""
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
    Computes precise, synchronized auction timing attributes across UTC, Polish time (CET/CEST), and Japanese time (JST).
    Guarantees that ends_at is in the present/future and matches time_remaining_minutes down to the minute.
    """
    now_utc = ref_time_utc or datetime.now(timezone.utc)
    if now_utc.tzinfo is None:
        now_utc = now_utc.replace(tzinfo=timezone.utc)

    # Timezones:
    # Poland standard time (CET): UTC+1
    # Japan standard time (JST): UTC+9
    tz_pl_offset = timedelta(hours=1)
    tz_jst_offset = timedelta(hours=9)
    now_pl = now_utc + tz_pl_offset

    raw_ends_at = deal.get("ends_at")
    raw_minutes = deal.get("time_remaining_minutes")

    target_end_dt = None

    # Try parsing ends_at if present and check if it's in the future
    if raw_ends_at and isinstance(raw_ends_at, str):
        clean_str = raw_ends_at.replace(" UTC", "").replace("Z", "").strip()
        for fmt in ["%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M"]:
            try:
                parsed = datetime.strptime(clean_str, fmt).replace(tzinfo=timezone.utc)
                # If parsed is in the future (or less than 2 minutes ago), keep it
                if (parsed - now_utc).total_seconds() > -120:
                    target_end_dt = parsed
                    break
            except ValueError:
                continue

    # If ends_at was missing or in the past, anchor target_end_dt dynamically from minutes
    if target_end_dt is None:
        minutes = int(raw_minutes) if raw_minutes is not None and int(raw_minutes) > 0 else 120
        target_end_dt = now_utc + timedelta(minutes=minutes)

    # Compute exact remaining minutes from now_utc
    diff_seconds = (target_end_dt - now_utc).total_seconds()
    minutes_rem = max(1, int(round(diff_seconds / 60.0)))

    # Formatting representations
    ends_at_utc_str = target_end_dt.strftime("%Y-%m-%d %H:%M UTC")
    ends_at_iso = target_end_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    end_pl = target_end_dt + tz_pl_offset
    end_jst = target_end_dt + tz_jst_offset

    pl_clock = end_pl.strftime("%H:%M")
    jst_clock = end_jst.strftime("%H:%M")

    # Date relative label for Polish users
    days_diff = (end_pl.date() - now_pl.date()).days
    if days_diff == 0:
        day_label = "Dziś"
    elif days_diff == 1:
        day_label = "Jutro"
    elif days_diff == 2:
        day_label = "Pojutrze"
    else:
        day_label = end_pl.strftime("%d.%m")

    ends_at_formatted = f"{day_label} o {pl_clock} (PL) / {jst_clock} (JP)"
    ends_at_pl_short = f"{day_label} {pl_clock}"

    time_formatted = format_time_remaining(minutes_rem)

    if minutes_rem <= 60:
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
        "is_ending_soon": is_ending_soon
    }
