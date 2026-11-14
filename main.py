#!/usr/bin/env python3
"""Main entrypoint for Japan Deal Watcher."""

import sys
import os
from pathlib import Path

_REPO_DIR = Path(__file__).resolve().parent
_VENV_DIR = _REPO_DIR / ".venv"
_VENV_PYTHON = _VENV_DIR / "bin" / "python"
if _VENV_PYTHON.exists() and Path(sys.prefix).resolve() != _VENV_DIR.resolve():
    os.execv(str(_VENV_PYTHON), [str(_VENV_PYTHON)] + sys.argv)

import json

from watcher.config import (
    WATCHLIST_FILE,
    CURRENT_DEALS_FILE,
    YAHOO_DEALS_FILE,
    YAHOO_MD_FILE,
    SNIPER_GUIDE_MD_FILE,
    MARKET_SALES_MD_FILE,
    AUCTION_RADAR_MD_FILE,
    MYSTERY_LOTS_MD_FILE,
    REPORTS_DIR,
    LATEST_REPORT_FILE,
    DOCS_DATA_FILE,
    BASE_DIR
)
from watcher.currency import get_live_rates
from watcher.fetcher import DealFetcher
from watcher.consolidation import ConsolidationTracker
from watcher.markdown_generator import MarkdownGenerator
from watcher.alternative_generator import AlternativeDealsGenerator
from watcher.sniper_guide_generator import SniperGuideGenerator
from watcher.auction_radar import AuctionRadarGenerator
from watcher.mystery_lots_generator import MysteryLotsGenerator
from watcher.webapp_exporter import WebappExporter
from watcher.history_tracker import HistoryTracker
from watcher.history_generator import HistoryGenerator
from watcher.finished_auctions_tracker import FinishedAuctionsTracker
from watcher.resale_ledger import ResaleLedger

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

    rate_jpy, rate_eur, is_live_jpy, is_live_eur = get_live_rates()
    if not is_live_jpy:
        rate_jpy = fallback_rate_jpy
    if not is_live_eur:
        rate_eur = fallback_rate_eur

    print(f"💱 Exchange rates: 100 JPY ≈ {rate_jpy * 100:.2f} PLN | 1 EUR ≈ {rate_eur:.4f} PLN")

    fetcher = DealFetcher(rate=rate_jpy, rate_eur=rate_eur)
    deals = fetcher.scan_watchlist(watchlist)

    with open(CURRENT_DEALS_FILE, "w", encoding="utf-8") as f:
        json.dump(deals, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved {len(deals)} deals to {CURRENT_DEALS_FILE}")

    start_date = settings.get("consolidation_start_date", "2026-11-07")
    storage_limit = settings.get("free_storage_days", 60)
    tracker = ConsolidationTracker(start_date=start_date, storage_limit_days=storage_limit)
    timeline = tracker.get_timeline_status()
    print(f"⏳ 60-Day Warehouse Storage: {timeline['days_remaining']} days remaining until {timeline['deadline']}")

    generator = MarkdownGenerator(
        deals=deals,
        timeline_status=timeline,
        rate=rate_jpy,
        rate_eur=rate_eur,
        is_live_rate=is_live_jpy
    )
    latest_report_content = generator.generate_latest_report()

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(LATEST_REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(latest_report_content)
    print(f"📄 Successfully generated and updated {LATEST_REPORT_FILE}")

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

        radar_generator = AuctionRadarGenerator(
            raw_deals=yahoo_deals,
            timeline_status=timeline,
            rate=rate_jpy,
            rate_eur=rate_eur,
            is_live_rate=is_live_jpy
        )
        radar_content = radar_generator.generate()
        with open(AUCTION_RADAR_MD_FILE, "w", encoding="utf-8") as f:
            f.write(radar_content)
        print(f"📄 Successfully generated and updated {AUCTION_RADAR_MD_FILE} (Live Auction Radar)")

        mystery_gen = MysteryLotsGenerator(
            raw_deals=yahoo_deals,
            timeline_status=timeline,
            rate=rate_jpy,
            rate_eur=rate_eur,
            is_live_rate=is_live_jpy
        )
        mystery_content = mystery_gen.generate()
        with open(MYSTERY_LOTS_MD_FILE, "w", encoding="utf-8") as f:
            f.write(mystery_content)
        print(f"📄 Successfully generated and updated {MYSTERY_LOTS_MD_FILE} (Danshari & Mystery Lots)")

        if os.environ.get("OBSIDIAN_VAULT_ENABLED") == "1":
            obsidian_mystery_path = Path("/home/borg/docker/obsidian/vault/20-reports/adhoc/2026-11-09-mystery-lots-analysis.md")
            if obsidian_mystery_path.parent.exists():
                try:
                    with open(obsidian_mystery_path, "w", encoding="utf-8") as f:
                        f.write(mystery_content)
                    print(f"📑 Copied mystery lots report to Obsidian: {obsidian_mystery_path.name}")
                except Exception as e:
                    print(f"[WARN] Obsidian copy skipped: {e}")

            obsidian_radar_path = Path("/home/borg/docker/obsidian/vault/20-reports/adhoc/2026-11-09-yahoo-auctions-radar.md")
            if obsidian_radar_path.parent.exists():
                try:
                    with open(obsidian_radar_path, "w", encoding="utf-8") as f:
                        f.write(radar_content)
                    print(f"📑 Copied auction radar to Obsidian: {obsidian_radar_path.name}")
                except Exception as e:
                    print(f"[WARN] Obsidian copy skipped: {e}")

    history_tracker = HistoryTracker()
    all_scan_deals = list(deals)
    if YAHOO_DEALS_FILE.exists():
        with open(YAHOO_DEALS_FILE, "r", encoding="utf-8") as f:
            y_deals = json.load(f)
        all_scan_deals.extend(y_deals)

    scan_stats = history_tracker.record_scan(all_scan_deals, rate_jpy=rate_jpy, rate_eur=rate_eur)
    print(f"📈 History Tracker: {scan_stats['total_sales']} closed sales recorded ({scan_stats['new_sales']} new, {scan_stats['total_tracked']} tracked items)")

    history_gen = HistoryGenerator(history_tracker)
    sales_md_content = history_gen.generate()
    with open(MARKET_SALES_MD_FILE, "w", encoding="utf-8") as f:
        f.write(sales_md_content)
    print(f"📄 Successfully generated and updated {MARKET_SALES_MD_FILE} (Market Sales & Price Intelligence)")

    if os.environ.get("OBSIDIAN_VAULT_ENABLED") == "1":
        obsidian_sales_path = Path("/home/borg/docker/obsidian/vault/20-reports/adhoc/2026-11-08-market-sales-history.md")
        if obsidian_sales_path.parent.exists():
            try:
                with open(obsidian_sales_path, "w", encoding="utf-8") as f:
                    f.write(sales_md_content)
                print(f"📑 Copied sales history report to Obsidian: {obsidian_sales_path.name}")
            except Exception as e:
                print(f"[WARN] Obsidian copy skipped: {e}")

    yahoo_deals_list = []
    if YAHOO_DEALS_FILE.exists():
        with open(YAHOO_DEALS_FILE, "r", encoding="utf-8") as f:
            yahoo_deals_list = json.load(f)

    finished_tracker = FinishedAuctionsTracker()
    finished_harvested = finished_tracker.harvest_from_active(yahoo_deals_list)
    finished_stats = finished_tracker.get_stats()
    print(f"🏁 Finished Auctions: {finished_stats['total_finished']} completed listings archived (Total Potential Arbitrage: +{finished_stats['total_potential_arbitrage_pln']:.2f} zł, Avg Arbitrage: +{finished_stats['avg_potential_arbitrage_pln']:.2f} zł)")

    webapp_exporter = WebappExporter(
        rate_jpy=rate_jpy,
        rate_eur=rate_eur,
        is_live_rate=is_live_jpy,
        timeline_status=timeline,
        mercari_deals=deals,
        yahoo_deals=yahoo_deals_list,
        history_stats=scan_stats,
        finished_tracker=finished_tracker
    )
    webapp_res = webapp_exporter.export(output_file=DOCS_DATA_FILE)
    print(f"📱 Webapp Exporter: Synced Android PWA data feed ({webapp_res['auctions_count']} auctions, {webapp_res['mercari_count']} Mercari deals, {finished_stats['total_finished']} finished auctions)")

    resale_ledger = ResaleLedger()
    ledger_metrics = resale_ledger.get_metrics()
    if ledger_metrics["total_items"] > 0:
        print(f"💼 Resale Ledger: {ledger_metrics['total_items']} items tracked | Capital at Risk: {ledger_metrics['capital_at_risk_pln']:.2f} zł | Realized Profit: +{ledger_metrics['total_realized_profit_pln']:.2f} zł (Win Rate: {ledger_metrics['win_rate_pct']}%)")

    print("=" * 60)

if __name__ == "__main__":
    main()
