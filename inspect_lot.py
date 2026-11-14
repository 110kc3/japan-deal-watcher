#!/usr/bin/env python3
"""CLI Tool: Japanese Mystery Game Lot & Danshari Photo Inspector.

Allows instant visual and textual inspection of mystery lots, Danshari decluttering boxes,
and bulk retro game auctions from Yahoo! Japan Auctions and Mercari.
"""

import sys
import json
import argparse
from pathlib import Path

from watcher.config import YAHOO_DEALS_FILE, CURRENT_DEALS_FILE
from watcher.lot_vision_inspector import LotVisionInspector, RETRO_GAME_KNOWLEDGE_BASE, DANSHARI_KEYWORDS

def load_all_deals():
    deals = []
    if YAHOO_DEALS_FILE.exists():
        with open(YAHOO_DEALS_FILE, "r", encoding="utf-8") as f:
            deals.extend(json.load(f))
    if CURRENT_DEALS_FILE.exists():
        with open(CURRENT_DEALS_FILE, "r", encoding="utf-8") as f:
            deals.extend(json.load(f))
    return deals

def cmd_list_lots():
    deals = load_all_deals()
    mystery_lots = []
    for d in deals:
        cat_id = d.get("category_id", "")
        danshari = LotVisionInspector.detect_danshari_type(" ".join([d.get("model", ""), d.get("search_query_jp", "")]))
        if "danshari" in cat_id or "retro_games" in cat_id or "mystery" in cat_id or danshari["is_mystery_lot"]:
            mystery_lots.append(d)

    print("=" * 80)
    print("📦 JAPAN DEAL WATCHER: PAKIETY RÓŻNOŚCI (DANSHARI / 処分 / 雑多 / 福袋)")
    print(f"Znaleziono {len(mystery_lots)} pakietów różności z potencjałem ukrytych skarbów")
    print("=" * 80)

    for i, lot in enumerate(mystery_lots, 1):
        inspection = LotVisionInspector.inspect_lot_photo_contents(lot)
        price_jpy = lot.get("price_jpy", 0)
        est_pl = lot.get("est_pl_value", 0)
        gems = inspection.get("top_gems", [])

        print(f"\n[{i}] {lot.get('model')}")
        print(f"    Platforma: {lot.get('platform')} | ID: {lot.get('id')}")
        print(f"    Cena w Japonii: {price_jpy:,} JPY | Wycena w PL: {est_pl:.0f} zł | Bateria: {lot.get('battery_type')}")
        print(f"    Typ partii: {inspection.get('lot_type_name')}")
        print(f"    {inspection.get('battery_notes')}")
        if gems:
            print(f"    💎 Wykryte perełki ({len(gems)} szt.):")
            for g in gems:
                print(f"       • {g['title']} ({g['platform']}) -> ~{g['est_pl_value']:.0f} zł w PL [{g['rarity']}]")
        if inspection.get("break_even_gem"):
            print(f"    💡 Break-Even: {inspection['break_even_gem']}")
        print(f"    🔗 Snajper: {lot.get('zenmarket_url', '')}")

def cmd_inspect_id(lot_id: str):
    deals = load_all_deals()
    target = None
    for d in deals:
        if d.get("id") == lot_id:
            target = d
            break

    if not target:
        print(f"❌ Nie znaleziono oferty o ID: {lot_id}")
        return

    inspection = LotVisionInspector.inspect_lot_photo_contents(target)
    print("=" * 80)
    print(f"🔍 INSPEKCJA WIZUALNA PAKIETU: {target.get('model')}")
    print("=" * 80)
    print(json.dumps(inspection, indent=2, ensure_ascii=False))
    print("\n--- FORMAT MARKDOWN ---")
    print(LotVisionInspector.format_inspection_markdown(inspection))

def cmd_analyze_text(text: str):
    print("=" * 80)
    print(f"📝 ANALIZA TEKSTU I TYTUŁU OFERTY: '{text}'")
    print("=" * 80)
    danshari = LotVisionInspector.detect_danshari_type(text)
    print(f"Typ aukcji: {danshari['label']} (Wykryto słowa kluczowe: {danshari.get('all_tags', [])})")
    print(f"Opis: {danshari['description']}")

    fake_deal = {"model": text, "custom_note": text, "price_jpy": 3000, "est_pl_value": 350.0}
    inspection = LotVisionInspector.inspect_lot_photo_contents(fake_deal)
    gems = inspection.get("top_gems", [])
    print(f"\n💎 Wykryte gry ({len(gems)} szt.):")
    for g in gems:
        print(f"  • {g['title']} ({g['platform']}) - Wycena: ~{g['est_pl_value']:.0f} zł [{g['rarity']}]")
    print(f"\n{inspection.get('battery_notes')}")

def cmd_demo():
    sample = "【断捨離】DS 3DS ゲームソフト 45本まとめ売り ポケットモンスター ハートゴールド プラチナ ゼルダの伝説 夢幻の砂時計 動作未確認 ジャンク扱い"
    print("🎬 URUCHAMIANIE DEMONSTRACJI INSPEKCJI PAKIETU DANSHARI...")
    cmd_analyze_text(sample)

def main():
    parser = argparse.ArgumentParser(description="Japanese Mystery Game Lot & Danshari Photo Inspector CLI")
    parser.add_argument("--list", action="store_true", help="Lista wszystkich śledzonych pakietów różności")
    parser.add_argument("--id", type=str, help="ID oferty do szczegółowej inspekcji wizualnej")
    parser.add_argument("--analyze", type=str, help="Tekst japońskiego tytułu lub opisu do analizy")
    parser.add_argument("--demo", action="store_true", help="Uruchom demonstrację na przykładowym pakiecie Danshari")

    if len(sys.argv) == 1:
        parser.print_help()
        return

    args = parser.parse_args()

    if args.list:
        cmd_list_lots()
    elif args.id:
        cmd_inspect_id(args.id)
    elif args.analyze:
        cmd_analyze_text(args.analyze)
    elif args.demo:
        cmd_demo()

if __name__ == "__main__":
    main()
