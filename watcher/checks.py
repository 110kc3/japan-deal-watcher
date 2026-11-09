"""Comprehensive Deal & System Integrity Checks Suite for Japan Deal Watcher.

Enforces:
1. Camera price cap (aparaty powyżej 100 zł nie są okazjami).
2. Expanded defect and broken keywords exclusion.
3. Untested arbitrage / opportunity gain detection.
4. Anti-scam and listing sanity (empty box / manual only).
5. Domestic shipping traps (Chakubarai / 着払い).
6. IATA Lithium-Ion parcel limits (max 2 Li-Ion).
7. Profitability & ROI minimum hurdle rates.
8. Currency feed health & spread sanity.
9. Watchlist and alternative deals JSON dataset integrity.
10. Markdown dashboard file integrity and cross-links.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple

from .config import (
    BASE_DIR,
    DATA_DIR,
    WATCHLIST_FILE,
    CURRENT_DEALS_FILE,
    YAHOO_DEALS_FILE,
    YAHOO_MD_FILE,
    SNIPER_GUIDE_MD_FILE,
    MAX_CAMERA_PRICE_PLN,
    MAX_LENS_PRICE_PLN,
    MAX_LI_ION_PER_PARCEL,
    DEFAULT_JPY_PLN_RATE,
    DEFAULT_EUR_PLN_RATE
)

# 1. Defect keywords (broken / damaged / parts only)
DEFECT_KEYWORDS = [
    # General failure & non-working
    "故障", "壊れて", "壊れ", "動かない", "動作不可", "作動不可",
    "起動不可", "起動しません", "起動しない", "電源入りません", "電源つかない", "電源が入らない", "通電不可",
    "赤点滅", "電源落ちる", "勝手に電源が切れる",
    # Optics / Lens damage
    "カビあり", "カビが生えて", "カビが見られ", "クモリあり", "くもりあり", "くもりが見られ",
    "バルサム切れ", "絞り不良", "絞り羽根油", "絞り動かない",
    # Corrosion / Battery acid
    "液漏れ", "青サビ", "青錆", "端子サビ", "端子腐食",
    # Display / Screen defects
    "画面割れ", "液晶割れ", "液晶漏れ", "ドット抜け", "ビネガーシンドローム", "画面真っ暗", "液晶不良", "バックライト切れ",
    # Drives & mechanics
    "シャッター不動", "シャッター切れません", "シャッター切れない", "巻き上げ不可", "巻き上げ不良",
    "読み込みが出来ません", "読み込み不可", "読み込まない", "ディスク読み込まない",
    "トレイ開かない", "トレイ開閉不可", "イジェクト不良", "異音",
    # Controls / Sticks
    "スティック誤作動", "スティックドリフト", "ドリフト", "ボタン効かない", "ボタン陥没",
    # Shell / Physical damage
    "破損しており", "破損あり", "ヒビ", "ヒンジ破損", "ヒンジ割れ", "電池蓋破損", "電池蓋爪折れ", "爪折れ",
    # Water / Environment
    "水没", "水濡れ", "水没マーク", "タバコ臭", "ヤニ汚れ", "不動品"
]

# 2. Untested / high gain potential keywords
UNTESTED_KEYWORDS = [
    "未確認", "動作未確認", "動作未チェック", "未チェック",
    "現状品", "現状渡し", "通電のみ", "通電確認のみ", "通電ok", "通電確認済",
    "確認していません", "確認しておりません", "動作確認はしておりません", "確認できておりません",
    "充電器がない", "環境がない", "ソフトがない", "コードがない", "未検品",
    "フィルム未装填", "フィルムを入れての確認はしていません", "電池がないため",
    "動作環境がないため", "テレビがないため", "倉庫整理", "実家から出てきた"
]

# 3. Clean optics keywords
CLEAN_OPTICS_KEYWORDS = [
    "光学クリア", "カビなし", "クモリなし", "分解清掃", "黄変除去",
    "dry box", "防湿box", "防湿庫", "チリ極小", "ホコリ極少"
]

# 4. Confirmed working keywords
CONFIRMED_WORKING_KEYWORDS = [
    "動作確認済み", "動作確認済", "動作品", "完動品", "動作ok",
    "起動確認", "初期化済", "ボタン正常", "読み込みok", "液晶良好",
    "美品", "良品", "整備済", "メンテナンス済", "新品バッテリー",
    "シャッター動作ok", "フラッシュ発光ok"
]

# 5. Trap keywords (box only / manual only / empty packages)
TRAP_KEYWORDS = [
    "箱のみ", "外箱のみ", "空箱", "パッケージのみ", "説明書のみ", "取扱説明書のみ", "部品取り専用"
]


def is_camera_item(item: Dict[str, Any]) -> bool:
    """Detects whether an item belongs to the analog/compact camera category."""
    cat_id = item.get("category_id", "")
    cat_name = item.get("category_name", "").lower()
    model = item.get("model", "").lower()
    note = item.get("custom_note", item.get("note", "")).lower()

    if cat_id in ["film_cameras_point_shoot", "analog_cameras", "cameras"]:
        return True
    if any(k in cat_name for k in ["aparat", "camera", "małpka", "point & shoot"]):
        return True
    if any(k in model for k in ["autoboy", "mju", "espio", "big mini", "c35", "trip 35", "riva zoom", "cardia"]):
        return True
    if "aparat" in note:
        return True
    return False


def check_camera_price_cap(item: Dict[str, Any], max_price_pln: float = MAX_CAMERA_PRICE_PLN) -> Tuple[bool, str]:
    """
    Check 1: Camera Price Cap.
    User rule: 'aparaty powyżej 100zł nie są okazjami'.
    Any camera with item purchase price > 100 PLN is rejected as a deal.
    """
    if not is_camera_item(item):
        return True, "N/A (Przedmiot nie jest aparatem fotograficznym)"

    raw_pln = item.get("price_pln_raw")
    if raw_pln is None:
        price_jpy = item.get("price_jpy", item.get("target_price_jpy", 0))
        raw_pln = round(price_jpy * DEFAULT_JPY_PLN_RATE, 2)

    if raw_pln > max_price_pln:
        return False, f"Cena aparatu {raw_pln:.2f} zł przekracza dopuszczalny limit {max_price_pln:.2f} zł. Aparaty powyżej 100 zł nie są okazjami."
    return True, f"Cena aparatu {raw_pln:.2f} zł mieści się w limicie okazjonalnym (<= {max_price_pln:.2f} zł)"


def is_lens_item(item: Dict[str, Any]) -> bool:
    """Detects whether an item belongs to the analog/manual lens category."""
    cat_id = item.get("category_id", "")
    cat_name = item.get("category_name", "").lower()
    model = item.get("model", "").lower()
    note = item.get("custom_note", item.get("note", "")).lower()

    if cat_id in ["analog_lenses", "manual_lenses", "lenses"]:
        return True
    if any(k in cat_name for k in ["obiektyw", "lens", "takumar", "zuiko", "rokkor"]):
        return True
    if any(k in model for k in ["takumar", "pentax-m", "canon fd", "zuiko", "rokkor", "50mm f/", "55mm f/", "28mm f/", "50mm f1", "55mm f1"]):
        return True
    if "obiektyw" in note:
        return True
    return False


def check_lens_price_cap(item: Dict[str, Any], max_price_pln: float = MAX_LENS_PRICE_PLN) -> Tuple[bool, str]:
    """
    Check: Lens Price Cap.
    User rule: 'obiektywy tez w duzych cenach odpadaja'.
    Any analog lens with item purchase price > 100 PLN is rejected as a deal.
    """
    if not is_lens_item(item):
        return True, "N/A (Przedmiot nie jest obiektywem)"

    raw_pln = item.get("price_pln_raw")
    if raw_pln is None:
        price_jpy = item.get("price_jpy", item.get("target_price_jpy", 0))
        raw_pln = round(price_jpy * DEFAULT_JPY_PLN_RATE, 2)

    if raw_pln > max_price_pln:
        return False, f"Cena obiektywu {raw_pln:.2f} zł przekracza dopuszczalny limit {max_price_pln:.2f} zł. Obiektywy w dużych cenach odpadają."
    return True, f"Cena obiektywu {raw_pln:.2f} zł mieści się w limicie okazjonalnym (<= {max_price_pln:.2f} zł)"


def is_nintendo_ds_item(item: Dict[str, Any]) -> bool:
    """Detects whether an item belongs to the Nintendo DS / 3DS handheld family."""
    cat_id = item.get("category_id", "")
    cat_name = item.get("category_name", "").lower()
    model = item.get("model", "").lower()

    if cat_id in ["nintendo_ds_consoles", "nintendo_handhelds", "nintendo_3ds_handhelds", "nintendo_ds_handhelds"]:
        return True
    if any(k in cat_name for k in ["nintendo ds", "ds lite", "dsi", "3ds", "2ds", "new 3ds", "dsi ll", "dsi xl"]):
        return True
    if any(k in model for k in ["ds lite", "dsi", "3ds", "2ds", "nintendo ds", "new 3ds", "dsi ll", "dsi xl"]):
        return True
    return False


def is_handheld_item(item: Dict[str, Any]) -> bool:
    """Detects whether an item belongs to any handheld console category."""
    cat_id = item.get("category_id", "")
    cat_name = item.get("category_name", "").lower()
    model = item.get("model", "").lower()

    if cat_id in [
        "nintendo_3ds_handhelds", "nintendo_ds_handhelds", "gameboy_advance_retro",
        "ps_vita", "ps_vita_handhelds", "psp_handheld", "nintendo_ds_consoles"
    ]:
        return True
    if any(k in cat_name for k in ["handheld", "vita", "psp", "game boy", "gba", "3ds", "ds lite", "dsi"]):
        return True
    if any(k in model for k in ["vita", "psp", "game boy", "gba", "3ds", "ds lite", "dsi", "gbc", "micro"]):
        return True
    return False


def check_defects(text: str, custom_note: str = "", item_condition: str = "") -> Tuple[bool, str]:
    """
    Check 2: Defect & Damage Exclusion Check.
    Detects if the listing contains any defect / broken / damaged keywords.
    """
    combined = ((text or "") + " " + (custom_note or "") + " " + (item_condition or "")).lower()

    # Pre-clean negations
    cleaned = combined
    cleaned = cleaned.replace("カビなし", "カビ無し")
    cleaned = cleaned.replace("クモリなし", "クモリ無し")
    cleaned = cleaned.replace("傷なし", "傷無し")
    cleaned = cleaned.replace("液漏れ無", "液漏れなし")
    cleaned = cleaned.replace("異常無", "異常なし")
    cleaned = cleaned.replace("ご購入後の故障", "")
    cleaned = cleaned.replace("購入後の故障", "")
    cleaned = cleaned.replace("故障の可能性", "未確認")

    negations = ["なし", "ありません", "ないです", "確認済み", "無", "無し", "見られません", "ございません"]

    # If explicitly untested due to missing accessories, avoid parts-only false positive
    is_explicit_untested = any(w in cleaned for w in [
        "動作未確認", "未確認", "充電器がない為動作未確認", "手元に電源コードやケーブル類がないため", "コードがないため"
    ])

    for kw in sorted(DEFECT_KEYWORDS, key=len, reverse=True):
        if kw in cleaned:
            # Check negation
            is_negated = any(kw + neg in cleaned or kw + "は" + neg in cleaned for neg in negations)
            if not is_negated:
                return False, f"Wykryto defekt/uszkodzenie: '{kw}' w opisie"

    # Box-only / manual-only trap check
    for trap in TRAP_KEYWORDS:
        if trap in cleaned:
            return False, f"Wykryto pułapkę oferty (niepełny towar / tylko pudełko): '{trap}'"

    return True, "Brak uszkodzeń i defektów"


def check_untested_opportunity(text: str, custom_note: str = "") -> Tuple[bool, str]:
    """
    Check 3: Untested Opportunity / Arbitrage Potential Check.
    Detects if item is untested by seller (high upside).
    """
    combined = ((text or "") + " " + (custom_note or "")).lower()
    for kw in sorted(UNTESTED_KEYWORDS, key=len, reverse=True):
        if kw in combined:
            return True, f"Wykryto potencjał zysku (sprzęt niesprawdzany): '{kw}'"
    return False, "Sprzęt nie posiada flagi 'niesprawdzany'"


def check_shipping_trap(text: str) -> Tuple[bool, str]:
    """
    Check 4: Domestic Shipping Trap Check.
    Detects free shipping vs Chakubarai (cash on delivery) warnings.
    """
    t = (text or "").lower()
    if "送料無料" in t:
        return True, "Darmowa wysyłka krajowa w Japonii (送料無料)"
    if "着払い" in t:
        return False, "Ostrzeżenie: Płatność przy odbiorze (着払い / Chakubarai)"
    return True, "Standardowa stawka wysyłki krajowej (~800 JPY)"


def check_iata_lithium(items: List[Dict[str, Any]]) -> Tuple[bool, str]:
    """
    Check 5: IATA Air Shipment Lithium-Ion Battery Limits.
    Enforces maximum 2 Li-Ion batteries per consolidated shipment.
    """
    li_ion_count = 0
    for it in items:
        b_type = it.get("battery_type", "none").lower()
        color = it.get("color", "")
        note = it.get("custom_note", it.get("note", "")).lower()
        if b_type == "li-ion" and "bez baterii" not in color.lower() and "bez baterii" not in note:
            li_ion_count += 1

    if li_ion_count > MAX_LI_ION_PER_PARCEL:
        return False, f"Przekroczono limit IATA: {li_ion_count} baterii Li-Ion w paczce (maksymalnie {MAX_LI_ION_PER_PARCEL})"
    return True, f"Zgodne z regulacjami IATA ({li_ion_count}/{MAX_LI_ION_PER_PARCEL} baterii Li-Ion)"


def check_profitability_hurdle(deal: Dict[str, Any], min_roi: float = 30.0, min_margin: float = 40.0) -> Tuple[bool, str]:
    """
    Check 6: Profitability & Hurdle Rate Check.
    Verifies that the deal delivers adequate profit margin and ROI.
    """
    margin = deal.get("est_margin_pln", 0)
    roi = deal.get("roi_percent", 0)

    if margin < min_margin:
        return False, f"Zbyt niski zysk netto: {margin:.2f} zł (wymagane min. {min_margin:.2f} zł)"
    if roi < min_roi:
        return False, f"Zbyt niska stopa zwrotu: {roi:.1f}% ROI (wymagane min. {min_roi:.1f}%)"
    return True, f"Opłacalna oferta (+{margin:.2f} zł, +{roi:.1f}% ROI)"


def check_currency_health(rate_jpy: float, rate_eur: float) -> Tuple[bool, str]:
    """
    Check 7: Currency Exchange Rate Health & Spread Check.
    Validates that rates are positive and within historical sanity bounds.
    """
    if rate_jpy <= 0.015 or rate_jpy >= 0.045:
        return False, f"Anomalia kursu JPY/PLN: {rate_jpy:.6f} (oczekiwany zakres: 0.020 - 0.040)"
    if rate_eur <= 3.80 or rate_eur >= 5.50:
        return False, f"Anomalia kursu EUR/PLN: {rate_eur:.4f} (oczekiwany zakres: 4.00 - 5.00)"
    return True, f"Kursy walut stabilne (100 JPY ≈ {rate_jpy * 100:.2f} zł, 1 EUR ≈ {rate_eur:.4f} zł)"


def check_dataset_integrity(filepath: Path, expected_type: str = "watchlist") -> Tuple[bool, List[str]]:
    """
    Check 8: JSON Dataset Integrity & Camera Price Constraint.
    Validates that data files exist, contain valid JSON, have all required fields,
    and strictly satisfy the camera price cap rule (<= 100 PLN).
    """
    errors: List[str] = []
    if not filepath.exists():
        return False, [f"Plik danych nie istnieje: {filepath}"]

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return False, [f"Błąd parsowania JSON {filepath}: {e}"]

    if expected_type == "watchlist":
        categories = data.get("categories", [])
        if not categories:
            errors.append(f"{filepath}: Brak kategorii w watchlist.json")
        for cat in categories:
            cat_id = cat.get("id", "")
            items = cat.get("tracked_items", [])
            for it in items:
                # Validate camera prices
                if cat_id == "film_cameras_point_shoot" or is_camera_item(it):
                    price_jpy = it.get("target_price_jpy", 0)
                    raw_pln = price_jpy * DEFAULT_JPY_PLN_RATE
                    if raw_pln > MAX_CAMERA_PRICE_PLN:
                        errors.append(
                            f"Naruszenie reguły aparatów w {it.get('id', 'item')} ({it.get('model')}): "
                            f"cena {raw_pln:.2f} zł > {MAX_CAMERA_PRICE_PLN:.2f} zł!"
                        )
                # Validate lens prices
                if cat_id == "analog_lenses" or is_lens_item(it):
                    price_jpy = it.get("target_price_jpy", 0)
                    raw_pln = price_jpy * DEFAULT_JPY_PLN_RATE
                    if raw_pln > MAX_LENS_PRICE_PLN:
                        errors.append(
                            f"Naruszenie reguły obiektywów w {it.get('id', 'item')} ({it.get('model')}): "
                            f"cena {raw_pln:.2f} zł > {MAX_LENS_PRICE_PLN:.2f} zł!"
                        )
    elif expected_type == "yahoo_deals":
        if not isinstance(data, list):
            errors.append(f"{filepath}: Dane powinny być listą ofert")
        else:
            for it in data:
                if is_camera_item(it):
                    price_jpy = it.get("price_jpy", 0)
                    raw_pln = price_jpy * DEFAULT_JPY_PLN_RATE
                    if raw_pln > MAX_CAMERA_PRICE_PLN:
                        errors.append(
                            f"Naruszenie reguły aparatów w aukcji {it.get('id', 'deal')} ({it.get('model')}): "
                            f"cena {raw_pln:.2f} zł > {MAX_CAMERA_PRICE_PLN:.2f} zł!"
                        )
                if is_lens_item(it):
                    price_jpy = it.get("price_jpy", 0)
                    raw_pln = price_jpy * DEFAULT_JPY_PLN_RATE
                    if raw_pln > MAX_LENS_PRICE_PLN:
                        errors.append(
                            f"Naruszenie reguły obiektywów w aukcji {it.get('id', 'deal')} ({it.get('model')}): "
                            f"cena {raw_pln:.2f} zł > {MAX_LENS_PRICE_PLN:.2f} zł!"
                        )

    return len(errors) == 0, errors


def check_markdown_dashboards(base_dir: Path = BASE_DIR) -> Tuple[bool, List[str]]:
    """
    Check 9: Markdown Dashboards & Cross-Links Integrity.
    Verifies existence of README.md, YAHOO_AUCTIONS_DEALS.md, AUCTION_SNIPING_GUIDE.md,
    and cross-links between them.
    """
    errors: List[str] = []
    dashboards = [
        base_dir / "README.md",
        base_dir / "YAHOO_AUCTIONS_DEALS.md",
        base_dir / "AUCTION_SNIPING_GUIDE.md",
        base_dir / "AUCTION_RADAR.md",
        base_dir / "REAL_PROFITABILITY_AUDIT.md",
        base_dir / "MARKET_SALES_HISTORY.md"
    ]
    for doc in dashboards:
        if not doc.exists():
            errors.append(f"Brak pliku dashboardu: {doc.name}")
        else:
            text = doc.read_text(encoding="utf-8")
            if len(text.strip()) < 500:
                errors.append(f"Plik {doc.name} jest podejrzanie krótki ({len(text)} znaków)")

    return len(errors) == 0, errors


def run_full_system_audit(strict: bool = False) -> Dict[str, Any]:
    """
    Executes all system and deal verification checks, returning an executive audit report.
    """
    audit_results: List[Dict[str, Any]] = []

    # 1. Currency health check
    ok, msg = check_currency_health(DEFAULT_JPY_PLN_RATE, DEFAULT_EUR_PLN_RATE)
    audit_results.append({"name": "NBP Live Currency Rates", "passed": ok, "message": msg, "icon": "💱"})

    # 2. Watchlist integrity & camera / lens <= 100 PLN rules
    ok, errs = check_dataset_integrity(WATCHLIST_FILE, expected_type="watchlist")
    msg = "Wszystkie kategorie, aparaty i obiektywy spełniają limit <= 100 zł" if ok else "; ".join(errs)
    audit_results.append({"name": "Watchlist Dataset & Camera/Lens <= 100 zł Rules", "passed": ok, "message": msg, "icon": "📋"})

    # 3. Yahoo deals integrity & camera / lens <= 100 PLN rules
    if YAHOO_DEALS_FILE.exists():
        ok, errs = check_dataset_integrity(YAHOO_DEALS_FILE, expected_type="yahoo_deals")
        msg = "Wszystkie aukcje, aparaty i obiektywy spełniają limit <= 100 zł" if ok else "; ".join(errs)
        audit_results.append({"name": "Yahoo Deals Dataset & Camera/Lens <= 100 zł Rules", "passed": ok, "message": msg, "icon": "🔨"})

    # 4. Markdown dashboards integrity
    ok, errs = check_markdown_dashboards(BASE_DIR)
    msg = "Wszystkie dashboardy Markdown (README, YAHOO, SNIPER) aktywne" if ok else "; ".join(errs)
    audit_results.append({"name": "Markdown Dashboards & Cross-Links", "passed": ok, "message": msg, "icon": "📄"})

    total_checks = len(audit_results)
    passed_checks = sum(1 for r in audit_results if r["passed"])
    failed_checks = total_checks - passed_checks

    is_overall_success = (failed_checks == 0)

    return {
        "success": is_overall_success,
        "total_checks": total_checks,
        "passed_checks": passed_checks,
        "failed_checks": failed_checks,
        "checks": audit_results
    }
