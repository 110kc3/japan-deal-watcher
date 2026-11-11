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

# NBP reference rates & tax parameters
DEFAULT_JPY_PLN_RATE = 0.024832  # 100 JPY ≈ 2.48 PLN
DEFAULT_EUR_PLN_RATE = 4.35      # 1 EUR ≈ 4.35 PLN

# ZenMarket fees & deposit rates
ZENMARKET_FEE_JPY = 800          # 800 JPY fee per item (domestic shipping / item charge)
ZENMARKET_FEE_EUR = 2.0          # 2 EUR fee per item (ZenMarket proxy / handling fee)
ZENMARKET_DEPOSIT_FEE_RATE = 0.035  # 3.5% deposit processing fee (Stripe / Card / PayPal)
ZENMARKET_BATTERY_DISPOSAL_FEE_JPY = 300  # 300 JPY disposal fee per battery/device
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
    "danshari_mystery_lots": 35.0,    # ~1.0-2.5kg Danshari / Mystery lots / Box assortment (0% Li-Ion)
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
    "film_cameras_point_shoot": 25.0,  # ~180-280g 35mm compact point-and-shoot camera
    "mechanical_keyboards": 45.0       # ~900-1400g mechanical keyboard / custom board (0% Li-Ion)
}
DEFAULT_SHIPPING_SHARE_PLN = 30.0

# Item estimated physical net weights (grams)
CATEGORY_ESTIMATED_WEIGHTS_G = {
    "nintendo_3ds_handhelds": 320,        # New 3DS XL ~330g, Old 3DS ~235g + sleeve
    "nintendo_ds_handhelds": 280,         # DS Lite ~218g, DSi LL ~314g
    "gameboy_advance_retro": 200,         # GBA SP ~142g, GBC ~138g
    "ps_vita": 290,                       # PS Vita 1000/2000 ~220-260g + sleeve
    "ps_vita_handhelds": 290,             # Alias
    "psp_handheld": 260,                  # PSP-3000 ~189g + charger
    "retro_games_mix": 350,               # Bundle of retro game cartridges/boxes
    "danshari_mystery_lots": 1800,        # Large mystery cardboard box / bulk lot
    "high_margin_curated_consoles": 2500, # PSone Combo + LCD ~1.8kg, PS4 Pro ~3.8kg
    "film_cameras_point_shoot": 260,      # Compact 35mm camera ~200g + pouch
    "mechanical_keyboards": 1150,         # Heavy aluminum/steel plate mechanical keyboard (0% Li-Ion)
    "analog_lenses": 280,                 # Manual prime lens ~200g + metal caps
    "ps5_limited_controllers": 380,       # DualSense ~280g + retail packaging
    "ps_retro_limited_controllers": 320,  # DualShock controller
    "ps1_consoles": 950,                  # PSone ~550g, PS1 fat ~1.2kg
    "retro_consoles_no_battery": 2200,    # Home console unit
    "nintendo_retro": 400,                # Game Boy / Famicom compact
    "nintendo_ds_consoles": 280,
    "ps_limited_consoles": 2800,
}
DEFAULT_ITEM_WEIGHT_G = 300
OUTER_BOX_BUFFER_WEIGHT_G = 300  # Sturdy cardboard outer shipping box + bubble wrap / cushioning
AVIA_MAX_WEIGHT_G = 2000         # 2.0 kg hard ceiling for AVIA Small Packet

# International Shipping Rates (Japan to Poland via ZenMarket)
# AVIA Small Packet (Air Economy): max 2,000g, 7-14 days
# EMS Express Air (Japan Post): up to 30kg, 3-6 days, express
# Surface Mail (Sea / Morska): up to 30kg, 60-90 days, lowest cost per kg for heavy parcels
SHIPPING_METHODS = {
    "avia_small_packet": {
        "id": "avia_small_packet",
        "name": "✈️ AVIA Small Packet",
        "description": "Ekonomiczna poczta lotnicza (7-14 dni). Najbardziej opłacalna do 2,000 g.",
        "max_weight_g": 2000,
        "base_jpy": 1200,      # Up to 100g
        "step_weight_g": 100,
        "step_jpy": 150
    },
    "ems_express": {
        "id": "ems_express",
        "name": "🚀 EMS Express Air",
        "description": "Ekspresowa przesyłka lotnicza Japan Post (3-6 dni) z pełnym śledzeniem i ubezpieczeniem.",
        "max_weight_g": 30000,
        "base_jpy": 3900,      # Up to 500g
        "step_weight_g": 500,
        "step_jpy": 700
    },
    "surface_sea": {
        "id": "surface_sea",
        "name": "🚢 Surface Mail (Morska)",
        "description": "Przesyłka kontenerowa drogą morską (60-90 dni). Tani transport dla ciężkich paczek (>3 kg).",
        "max_weight_g": 30000,
        "base_jpy": 3300,      # Up to 1,000g
        "step_weight_g": 1000,
        "step_jpy": 450
    }
}

# HTTP Request headers
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
REQUEST_TIMEOUT = 12
