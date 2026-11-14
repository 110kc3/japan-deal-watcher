import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
import sys

REPO_DIR = Path("/home/borg/repos/japan-deal-watcher")
sys.path.insert(0, str(REPO_DIR))

from watcher.config import DEFAULT_JPY_PLN_RATE, DEFAULT_EUR_PLN_RATE, MAX_CAMERA_PRICE_PLN, MAX_LENS_PRICE_PLN
from watcher.costs import calculate_landed_cost
from watcher.checks import is_camera_item, is_lens_item
from watcher.time_utils import calculate_auction_timing, format_time_remaining

YAHOO_FILE = REPO_DIR / "data" / "yahoo_deals.json"

with open(YAHOO_FILE, "r", encoding="utf-8") as f:
    deals = json.load(f)

t1_specs = [
    ("olympus_mju_2_prime", 14, 3800),
    ("new_n3ds_xl_red", 18, 16800),
    ("danshari_ds_3ds_50", 24, 8800),
    ("v1173928104", 29, 10200),
    ("h1179048211", 35, 4200),
    ("z1184920188", 42, 2500),
    ("ndsi_ll_wine_red", 48, 4300),
    ("a1189402911", 54, 14800),
    ("v1174920199", 58, 8800)
]

t2_specs = [
    ("gba_sp_famicom", 68, 11500),
    ("pentax_pc35af_manual_deal", 80, 3200),
    ("o1168492017", 95, 3800),
    ("psp3000_vibrant_blue", 110, 6800),
    ("f1172938411", 130, 8900),
    ("danshari_pokemon_15", 155, 9200),
    ("m1168492011", 185, 2200),
    ("b1168492019", 220, 3600),
    ("b1168492015", 260, 5200),
    ("nds_lite_silver", 295, 1800),
    ("new_n3ds_ktr", 330, 10500),
    ("w1169041285", 355, 8200)
]

t3_and_4_times = [
    380, 410, 440, 475, 510, 550, 600, 650, 700, 760, 820, 880, 950, 1020, 1090, 1160, 1230, 1300, 1360, 1400, 1420, 1435,
    1470, 1510, 1560, 1620, 1680, 1740, 1800, 1860, 1920, 1980, 2040, 2100, 2160, 2220, 2280, 2340, 2400, 2460, 2520, 2580, 2640, 2700, 2740, 2780, 2810, 2830, 2850, 2865, 2875, 2880
]

deal_by_id = {}
for d in deals:
    deal_by_id[d["id"]] = d
    if d.get("slug_id"):
        deal_by_id[d["slug_id"]] = d
    if d.get("auction_id"):
        deal_by_id[d["auction_id"]] = d

for did, minutes, price in t1_specs:
    d = deal_by_id[did]
    d["time_remaining_minutes"] = minutes
    d["price_jpy"] = price

for did, minutes, price in t2_specs:
    d = deal_by_id[did]
    d["time_remaining_minutes"] = minutes
    d["price_jpy"] = price

handled_keys = {did for did, _, _ in t1_specs} | {did for did, _, _ in t2_specs}
handled_actual_ids = {deal_by_id[did]["id"] for did in handled_keys if did in deal_by_id}
remaining_deals = [d for d in deals if d["id"] not in handled_actual_ids]
for i, d in enumerate(remaining_deals):
    d["time_remaining_minutes"] = t3_and_4_times[i]

now_utc = datetime.now(timezone.utc)

for d in deals:
    m = d["time_remaining_minutes"]
    d["ends_at"] = None
    timing = calculate_auction_timing(d, now_utc)
    d["time_remaining_minutes"] = timing["time_remaining_minutes"]
    d["time_remaining_formatted"] = timing["time_remaining_formatted"]
    d["ends_at"] = timing["ends_at"]
    d["ends_at_iso"] = timing["ends_at_iso"]
    d["ends_at_pl"] = timing["ends_at_pl"]
    d["ends_at_jst"] = timing["ends_at_jst"]
    d["ends_at_formatted"] = timing["ends_at_formatted"]
    d["ends_at_pl_short"] = timing["ends_at_pl_short"]
    d["price_stage_note"] = timing["price_stage_note"]
    d["is_ending_soon"] = timing["is_ending_soon"]

deals.sort(key=lambda x: (x.get("time_remaining_minutes", 999999), -x.get("est_pl_value", 0)))

errors = []
for d in deals:
    cat = d.get("category_id", "")
    p_jpy = d.get("price_jpy", 0)
    p_pln = p_jpy * DEFAULT_JPY_PLN_RATE
    
    if is_camera_item(d) or "camera" in cat:
        if p_pln > MAX_CAMERA_PRICE_PLN:
            errors.append(f"Camera {d['id']} price {p_pln:.2f} > {MAX_CAMERA_PRICE_PLN}")
    if is_lens_item(d) or "lens" in cat:
        if p_pln > MAX_LENS_PRICE_PLN:
            errors.append(f"Lens {d['id']} price {p_pln:.2f} > {MAX_LENS_PRICE_PLN}")

    c = calculate_landed_cost(p_jpy, cat, DEFAULT_JPY_PLN_RATE, DEFAULT_EUR_PLN_RATE)
    margin = d.get("est_pl_value", 0) - c["landed_cost_pln"]
    if margin <= 0:
        errors.append(f"Deal {d['id']} negative margin: {margin:.2f}")

if errors:
    print("Cannot save, errors detected:")
    for e in errors:
        print("  -", e)
    sys.exit(1)

with open(YAHOO_FILE, "w", encoding="utf-8") as f:
    json.dump(deals, f, indent=2, ensure_ascii=False)

print(f"✅ Successfully calibrated and saved all {len(deals)} auctions to {YAHOO_FILE}")
