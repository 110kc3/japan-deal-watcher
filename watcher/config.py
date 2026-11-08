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

# Category-aware estimated shipping share in consolidated parcel (PLN)
CATEGORY_SHIPPING_SHARES = {
    "ps_vita": 35.0,                  # ~220g handheld
    "psp_go": 30.0,                   # ~158g compact slider handheld
    "psp_handheld": 30.0,             # ~190g handheld
    "psp_games_mix": 20.0,            # ~120-180g UMD lots
    "retro_consoles_no_battery": 65.0, # ~1.5-2.0kg Sega/Sony home console
    "ps1_consoles": 45.0,             # ~550g PSone to 1.2kg PS1 fat
    "nintendo_retro": 40.0,           # ~150g GBC to 800g Super Famicom
    "analog_lenses": 25.0,            # ~200g prime lens
    "ps5_limited_controllers": 30.0,  # ~280g DualSense controller
    "ps_retro_limited_controllers": 30.0, # ~210-280g DualShock 1-4 controller
    "ps_limited_consoles": 60.0,       # ~1.2-3.0kg PS1-PS5 special edition console
    "film_cameras_point_shoot": 25.0   # ~180-280g 35mm compact point-and-shoot camera
}
DEFAULT_SHIPPING_SHARE_PLN = 30.0

# HTTP Request headers
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
REQUEST_TIMEOUT = 12
