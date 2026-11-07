"""Configuration settings for Japan Deal Watcher."""

from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
WATCHLIST_FILE = DATA_DIR / "watchlist.json"
CURRENT_DEALS_FILE = DATA_DIR / "current_deals.json"

# NBP reference rates & tax parameters
DEFAULT_JPY_PLN_RATE = 0.024832  # 100 JPY ≈ 2.48 PLN
ZENMARKET_FEE_JPY = 500          # 500 JPY proxy fee per won auction
VAT_RATE = 0.23                  # 23% Polish VAT

# ZenMarket Free Storage Policy
FREE_STORAGE_DAYS = 60
# Consolidation cycle start date (2026-11-07)
CONSOLIDATION_START = datetime(2026, 11, 7)

# IATA Air Shipment Lithium Battery Regulations
MAX_LI_ION_PER_PARCEL = 2

# HTTP Request headers
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
REQUEST_TIMEOUT = 12
