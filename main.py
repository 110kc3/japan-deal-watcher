#!/usr/bin/env python3
"""Main entrypoint for Japan Deal Watcher."""

import json
import sys
from pathlib import Path

from watcher.config import WATCHLIST_FILE, CURRENT_DEALS_FILE, BASE_DIR
from watcher.fetcher import DealFetcher
from watcher.consolidation import ConsolidationTracker
from watcher.markdown_generator import MarkdownGenerator

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
    rate = settings.get("currency_rate_jpy_pln", 0.024832)

    # 1. Fetch deal data
    fetcher = DealFetcher(rate=rate)
    deals = fetcher.scan_watchlist(watchlist)

    # 2. Save current deals to JSON
    with open(CURRENT_DEALS_FILE, "w", encoding="utf-8") as f:
        json.dump(deals, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved {len(deals)} deals to {CURRENT_DEALS_FILE}")

    # 3. Calculate consolidation timeline
    tracker = ConsolidationTracker()
    timeline = tracker.get_timeline_status()
    print(f"⏳ 60-Day Warehouse Storage: {timeline['days_remaining']} days remaining until {timeline['deadline']}")

    # 4. Generate README.md
    generator = MarkdownGenerator(deals=deals, timeline_status=timeline, rate=rate)
    readme_content = generator.generate()

    readme_path = BASE_DIR / "README.md"
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme_content)
    print(f"📄 Successfully generated and updated {readme_path}")
    print("=" * 60)

if __name__ == "__main__":
    main()
