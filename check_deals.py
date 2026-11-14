#!/usr/bin/env python3
"""CLI tool to run comprehensive system and deal verification checks for Japan Deal Watcher."""

import sys
import argparse
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from watcher.checks import (
    run_full_system_audit,
    check_camera_price_cap,
    check_lens_price_cap,
    check_defects,
    check_iata_lithium,
    is_camera_item,
    is_lens_item
)
from watcher.config import CURRENT_DEALS_FILE, MAX_CAMERA_PRICE_PLN, MAX_LENS_PRICE_PLN

def main():
    parser = argparse.ArgumentParser(description="Japan Deal Watcher Verification Checks Audit")
    parser.add_argument("--strict", action="store_true", help="Exit with code 1 if any check fails")
    args = parser.parse_args()

    print("=" * 70)
    print("🔍 JAPAN DEAL WATCHER – SYSTEM & DEAL VERIFICATION AUDIT")
    print("=" * 70)

    audit = run_full_system_audit(strict=args.strict)
    has_errors = False

    for c in audit["checks"]:
        status = "✅ PASS" if c["passed"] else "❌ FAIL"
        if not c["passed"]:
            has_errors = True
        print(f"[{status}] {c['icon']} {c['name']}")
        print(f"         └─ {c['message']}")

    if CURRENT_DEALS_FILE.exists():
        try:
            with open(CURRENT_DEALS_FILE, "r", encoding="utf-8") as f:
                deals = json.load(f)

            active_deals = [d for d in deals if "Dostępne" in d.get("status", "")]
            camera_deals = [d for d in active_deals if is_camera_item(d)]

            overpriced_cameras = [
                d for d in camera_deals
                if d.get("price_pln_raw", 0) > MAX_CAMERA_PRICE_PLN
            ]
            if overpriced_cameras:
                has_errors = True
                print(f"[❌ FAIL] 📷 Live Camera Deals Price Cap Check (Max {MAX_CAMERA_PRICE_PLN:.2f} zł)")
                for oc in overpriced_cameras:
                    print(f"         └─ Przekroczono limit: {oc.get('model')} ({oc.get('price_pln_raw', 0):.2f} zł > 100 zł)")
            else:
                print(f"[✅ PASS] 📷 Live Camera Deals Price Cap Check: Wszystkie {len(camera_deals)} aparatów <= 100 zł!")

            lens_deals = [d for d in active_deals if is_lens_item(d)]
            overpriced_lenses = [
                d for d in lens_deals
                if d.get("price_pln_raw", 0) > MAX_LENS_PRICE_PLN
            ]
            if overpriced_lenses:
                has_errors = True
                print(f"[❌ FAIL] 🔍 Live Lens Deals Price Cap Check (Max {MAX_LENS_PRICE_PLN:.2f} zł)")
                for ol in overpriced_lenses:
                    print(f"         └─ Przekroczono limit: {ol.get('model')} ({ol.get('price_pln_raw', 0):.2f} zł > 100 zł)")
            else:
                print(f"[✅ PASS] 🔍 Live Lens Deals Price Cap Check: Wszystkie {len(lens_deals)} obiektywów <= 100 zł!")

            broken_active = [d for d in active_deals if d.get("is_broken")]
            if broken_active:
                has_errors = True
                print(f"[❌ FAIL] 🚫 Defect Exclusion Check: {len(broken_active)} uszkodzonych ofert oznaczonych jako aktywne!")
            else:
                print(f"[✅ PASS] 🚫 Defect Exclusion Check: 0 uszkodzonych ofert w puli aktywnej.")

        except Exception as e:
            print(f"[⚠️ WARN] Błąd odczytu current_deals.json: {e}")

    print("=" * 70)
    if has_errors:
        print("❌ WYNIK AUDYTU: Wykryto naruszenia reguł lub błędne dane!")
        print("=" * 70)
        if args.strict:
            sys.exit(1)
    else:
        print(f"🎉 WYNIK AUDYTU: Wszystkie checki zaliczone pomyślnie! (0 błędów)")
        print("=" * 70)
        sys.exit(0)

if __name__ == "__main__":
    main()
