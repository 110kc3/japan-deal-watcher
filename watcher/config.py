"""Configuration settings for Japan Deal Watcher."""

from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
WATCHLIST_FILE = DATA_DIR / "watchlist.json"
CURRENT_DEALS_FILE = DATA_DIR / "current_deals.json"
PRICE_HISTORY_FILE = DATA_DIR / "price_history.json"
FINISHED_AUCTIONS_FILE = DATA_DIR / "finished_auctions.json"
RESALE_LEDGER_FILE = DATA_DIR / "resale_ledger.json"
RESALE_LEDGER_CSV_FILE = DATA_DIR / "resale_ledger.csv"
ALERTS_HISTORY_FILE = DATA_DIR / "alerts_history.json"
YAHOO_DEALS_FILE = DATA_DIR / "yahoo_deals.json"
YAHOO_MD_FILE = BASE_DIR / "YAHOO_AUCTIONS_DEALS.md"
SNIPER_GUIDE_MD_FILE = BASE_DIR / "AUCTION_SNIPING_GUIDE.md"
MARKET_SALES_MD_FILE = BASE_DIR / "MARKET_SALES_HISTORY.md"
AUCTION_RADAR_MD_FILE = BASE_DIR / "AUCTION_RADAR.md"
MYSTERY_LOTS_MD_FILE = BASE_DIR / "MYSTERY_LOTS_ANALYSIS.md"
REPORTS_DIR = BASE_DIR / "reports"
LATEST_REPORT_FILE = REPORTS_DIR / "latest.md"
DOCS_DIR = BASE_DIR / "docs"
DOCS_DATA_FILE = DOCS_DIR / "data" / "deals.json"

DEFAULT_JPY_PLN_RATE = 0.024832
DEFAULT_EUR_PLN_RATE = 4.35

ZENMARKET_FEE_JPY = 800
ZENMARKET_FEE_EUR = 2.0
ZENMARKET_DEPOSIT_FEE_RATE = 0.035
ZENMARKET_BATTERY_DISPOSAL_FEE_JPY = 300
VAT_RATE = 0.23

FREE_STORAGE_DAYS = 60
CONSOLIDATION_START = datetime(2026, 11, 7)

MAX_LI_ION_PER_PARCEL = 2

MAX_CAMERA_PRICE_PLN = 100.0
MAX_LENS_PRICE_PLN = 100.0

CATEGORY_SHIPPING_SHARES = {
    "nintendo_switch_lite": 30.0,
    "nintendo_switch": 45.0,
    "nintendo_3ds_handhelds": 30.0,
    "nintendo_ds_handhelds": 30.0,
    "gameboy_advance_retro": 25.0,
    "ps_vita": 35.0,
    "ps_vita_handhelds": 35.0,
    "psp_handheld": 30.0,
    "retro_games_mix": 20.0,
    "danshari_mystery_lots": 35.0,
    "high_margin_curated_consoles": 65.0,
    "psp_games_mix": 20.0,
    "retro_consoles_no_battery": 65.0,
    "ps1_consoles": 45.0,
    "nintendo_retro": 40.0,
    "nintendo_ds_consoles": 30.0,
    "analog_lenses": 25.0,
    "ps5_limited_controllers": 30.0,
    "ps_retro_limited_controllers": 30.0,
    "ps_limited_consoles": 60.0,
    "film_cameras_point_shoot": 25.0,
    "mechanical_keyboards": 45.0
}
DEFAULT_SHIPPING_SHARE_PLN = 30.0

CATEGORY_ESTIMATED_WEIGHTS_G = {
    "nintendo_switch_lite": 350,
    "nintendo_switch": 1000,
    "nintendo_3ds_handhelds": 320,
    "nintendo_ds_handhelds": 280,
    "gameboy_advance_retro": 200,
    "ps_vita": 290,
    "ps_vita_handhelds": 290,
    "psp_handheld": 260,
    "retro_games_mix": 350,
    "danshari_mystery_lots": 1800,
    "high_margin_curated_consoles": 2500,
    "film_cameras_point_shoot": 260,
    "mechanical_keyboards": 1150,
    "analog_lenses": 280,
    "ps5_limited_controllers": 380,
    "ps_retro_limited_controllers": 320,
    "ps1_consoles": 950,
    "retro_consoles_no_battery": 2200,
    "nintendo_retro": 400,
    "nintendo_ds_consoles": 280,
    "ps_limited_consoles": 2800,
}
DEFAULT_ITEM_WEIGHT_G = 300
OUTER_BOX_BUFFER_WEIGHT_G = 300
AVIA_MAX_WEIGHT_G = 2000

SHIPPING_METHODS = {
    "avia_small_packet": {
        "id": "avia_small_packet",
        "name": "✈️ AVIA Small Packet",
        "description": "Ekonomiczna poczta lotnicza (7-14 dni). Najbardziej opłacalna do 2,000 g.",
        "max_weight_g": 2000,
        "base_jpy": 1200,
        "step_weight_g": 100,
        "step_jpy": 150
    },
    "ems_express": {
        "id": "ems_express",
        "name": "🚀 EMS Express Air",
        "description": "Ekspresowa przesyłka lotnicza Japan Post (3-6 dni) z pełnym śledzeniem i ubezpieczeniem.",
        "max_weight_g": 30000,
        "base_jpy": 3900,
        "step_weight_g": 500,
        "step_jpy": 700
    },
    "surface_sea": {
        "id": "surface_sea",
        "name": "🚢 Surface Mail (Morska)",
        "description": "Przesyłka kontenerowa drogą morską (60-90 dni). Tani transport dla ciężkich paczek (>3 kg).",
        "max_weight_g": 30000,
        "base_jpy": 3300,
        "step_weight_g": 1000,
        "step_jpy": 450
    }
}

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
REQUEST_TIMEOUT = 12
