"""Configuration settings for Japan Deal Watcher."""

from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
WATCHLIST_FILE = DATA_DIR / "watchlist.json"
CURRENT_DEALS_FILE = DATA_DIR / "current_deals.json"
PRICE_HISTORY_FILE = DATA_DIR / "price_history.json"
YAHOO_DEALS_FILE = DATA_DIR / "yahoo_deals.json"
YAHOO_MD_FILE = BASE_DIR / "YAHOO_AUCTIONS_DEALS.md"
SNIPER_GUIDE_MD_FILE = BASE_DIR / "AUCTION_SNIPING_GUIDE.md"
MARKET_SALES_MD_FILE = BASE_DIR / "MARKET_SALES_HISTORY.md"
AUCTION_RADAR_MD_FILE = BASE_DIR / "AUCTION_RADAR.md"

# NBP reference rates & tax parameters
DEFAULT_JPY_PLN_RATE = 0.024832  # 100 JPY ≈ 2.48 PLN
DEFAULT_EUR_PLN_RATE = 4.35      # 1 EUR ≈ 4.35 PLN

# ZenMarket fees & deposit rates
ZENMARKET_FEE_JPY = 800          # 800 JPY fee per item (domestic shipping / item charge)
ZENMARKET_FEE_EUR = 2.0          # 2 EUR fee per item (ZenMarket proxy / handling fee)
ZENMARKET_DEPOSIT_FEE_RATE = 0.035  # 3.5% deposit processing fee (Stripe / Card / PayPal)
VAT_RATE = 0.23                  # 23% Polish VAT

# ZenMarket Free Storage Policy
FREE_STORAGE_DAYS = 60
# Consolidation cycle start date (2026-11-07)
CONSOLIDATION_START = datetime(2026, 11, 7)

# IATA Air Shipment Lithium Battery Regulations
MAX_LI_ION_PER_PARCEL = 2

# Camera & Lens deals strict price cap (PLN)
# User rules: "aparaty powyżej 100zł nie są okazjami", "obiektywy tez w duzych cenach odpadaja"
MAX_CAMERA_PRICE_PLN = 100.0
MAX_LENS_PRICE_PLN = 100.0

# Category-aware estimated shipping share in consolidated parcel (PLN)
CATEGORY_SHIPPING_SHARES = {
    # Granular Handhelds (Grupa 1: "Płynne Złoto" i Grupa 2)
    "nintendo_3ds_handhelds": 30.0,   # ~250g 3DS to 330g New 3DS XL
    "nintendo_ds_handhelds": 30.0,    # ~218g DS Lite to 314g DSi LL
    "gameboy_advance_retro": 25.0,    # ~140g GBA SP to 160g GBC
    "ps_vita": 35.0,                  # ~220g handheld
    "ps_vita_handhelds": 35.0,        # Alias
    "psp_handheld": 30.0,             # ~190g handheld
    "retro_games_mix": 20.0,          # ~150-300g mixed retro game lots (0% Li-Ion)
    "high_margin_curated_consoles": 65.0, # ~1.2-4.0kg PSone Combo / PS4 Pro Rathalos CIB
    # Legacy & peripheral categories
    "psp_games_mix": 20.0,            # Legacy alias
    "retro_consoles_no_battery": 65.0, # ~1.5-2.0kg Sega/Sony home console
    "ps1_consoles": 45.0,             # ~550g PSone to 1.2kg PS1 fat
    "nintendo_retro": 40.0,           # ~150g GBC to 800g Super Famicom
    "nintendo_ds_consoles": 30.0,     # ~218g DS Lite to 314g DSi LL
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
