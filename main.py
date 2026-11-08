#!/usr/bin/env python3
"""Main entrypoint for Japan Deal Watcher."""

import json
import sys
from pathlib import Path

from watcher.config import (
    WATCHLIST_FILE,
    CURRENT_DEALS_FILE,
    YAHOO_DEALS_FILE,
    YAHOO_MD_FILE,
    SNIPER_GUIDE_MD_FILE,
    BASE_DIR
)
from watcher.currency import get_live_rates
from watcher.fetcher import DealFetcher
from watcher.consolidation import ConsolidationTracker
from watcher.markdown_generator import MarkdownGenerator
from watcher.alternative_generator import AlternativeDealsGenerator
from watcher.sniper_guide_generator import SniperGuideGenerator

def main():
    print("=" * 60)
    print("🇯🇵 Japan Deal Watcher & Consolidation Dashboard Runner")
    print("=" * 60)

    if not WATCHLIST_FILE.exists():
        print(f"Error: Watchlist file not found at {WATCHLIST_FILE}")
        sys.exit(1)

    with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
        watchlist = json.load(f)

    settings = watchlist.get("settings", {})
    fallback_rate_jpy = settings.get("currency_rate_jpy_pln", 0.024832)
    fallback_rate_eur = settings.get("currency_rate_eur_pln", 4.35)

    # 1. Fetch live NBP rates or fallback
    rate_jpy, rate_eur, is_live_jpy, is_live_eur = get_live_rates()
    if not is_live_jpy:
        rate_jpy = fallback_rate_jpy
    if not is_live_eur:
        rate_eur = fallback_rate_eur

    print(f"💱 Exchange rates: 100 JPY ≈ {rate_jpy * 100:.2f} PLN | 1 EUR ≈ {rate_eur:.4f} PLN")

    # 2. Fetch deal data
    fetcher = DealFetcher(rate=rate_jpy, rate_eur=rate_eur)
    deals = fetcher.scan_watchlist(watchlist)

    # 3. Save current deals to JSON
    with open(CURRENT_DEALS_FILE, "w", encoding="utf-8") as f:
        json.dump(deals, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved {len(deals)} deals to {CURRENT_DEALS_FILE}")

    # 4. Calculate consolidation timeline
    start_date = settings.get("consolidation_start_date", "2026-11-07")
    storage_limit = settings.get("free_storage_days", 60)
    tracker = ConsolidationTracker(start_date=start_date, storage_limit_days=storage_limit)
    timeline = tracker.get_timeline_status()
    print(f"⏳ 60-Day Warehouse Storage: {timeline['days_remaining']} days remaining until {timeline['deadline']}")

    # 5. Generate README.md
    generator = MarkdownGenerator(
        deals=deals,
        timeline_status=timeline,
        rate=rate_jpy,
        rate_eur=rate_eur,
        is_live_rate=is_live_jpy
    )
    readme_content = generator.generate()

    readme_path = BASE_DIR / "README.md"
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme_content)
    print(f"📄 Successfully generated and updated {readme_path}")

    # 6. Generate YAHOO_AUCTIONS_DEALS.md (Alternative marketplaces)
    if YAHOO_DEALS_FILE.exists():
        with open(YAHOO_DEALS_FILE, "r", encoding="utf-8") as f:
            yahoo_deals = json.load(f)
        alt_generator = AlternativeDealsGenerator(
            raw_deals=yahoo_deals,
            timeline_status=timeline,
            rate=rate_jpy,
            rate_eur=rate_eur,
            is_live_rate=is_live_jpy
        )
        yahoo_md_content = alt_generator.generate()
        with open(YAHOO_MD_FILE, "w", encoding="utf-8") as f:
            f.write(yahoo_md_content)
        print(f"📄 Successfully generated and updated {YAHOO_MD_FILE} ({len(yahoo_deals)} alternative deals)")

        # 7. Generate AUCTION_SNIPING_GUIDE.md (Tactical sniping masterclass & hard caps)
        sniper_generator = SniperGuideGenerator(
            raw_deals=yahoo_deals,
            timeline_status=timeline,
            rate=rate_jpy,
            rate_eur=rate_eur,
            is_live_rate=is_live_jpy
        )
        sniper_guide_content = sniper_generator.generate()
        with open(SNIPER_GUIDE_MD_FILE, "w", encoding="utf-8") as f:
            f.write(sniper_guide_content)
        print(f"📄 Successfully generated and updated {SNIPER_GUIDE_MD_FILE} (Tactical Sniping Guide)")

    print("=" * 60)

if __name__ == "__main__":
    main()
