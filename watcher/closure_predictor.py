"""Auction Closure Price Prediction Engine & Condition Analyzer (落札相場).

Predicts auction closing prices based on physical condition grading
and historical closed sales data, evaluating market deal viability.
"""

from typing import Dict, Any, List

from .config import (
    DEFAULT_JPY_PLN_RATE,
    DEFAULT_EUR_PLN_RATE,
    MAX_CAMERA_PRICE_PLN,
    MAX_LENS_PRICE_PLN
)
from .costs import calculate_landed_cost, calculate_max_sniper_bid
from .checks import is_camera_item, is_lens_item


class ConditionGrade:
    """Standardized Condition Grades for Japanese Auctions."""
    MINT_BOX = "A_MINT_BOX"
    VERY_GOOD = "B_VERY_GOOD"
    GOOD_CONSOLE_ONLY = "C_GOOD_CONSOLE_ONLY"
    FLAWED_WORKING = "D_FLAWED_WORKING"
    UNTESTED_JUNK = "J_UNTESTED_JUNK"

    DETAILS = {
        MINT_BOX: {
            "label": "📦 Kolekcjonerski Box (CIB)",
            "short_label": "Box CIB",
            "multiplier": 1.08,
            "badge_color": "#8b5cf6",  # purple
            "desc": "Stan gabinetowy/kolekcjonerski w oryginalnym pudełku z kompletem akcesoriów"
        },
        VERY_GOOD: {
            "label": "✨ Bardzo Dobry (Sprawny 100%)",
            "short_label": "B. Dobry",
            "multiplier": 1.00,
            "badge_color": "#10b981",  # emerald
            "desc": "Zadbany egzemplarz, w 100% sprawny technicznie, czysty ekran, minimalne ślady"
        },
        GOOD_CONSOLE_ONLY: {
            "label": "🎮 Sprawny (Goła konsola)",
            "short_label": "Goła Konsola",
            "multiplier": 0.90,
            "badge_color": "#3b82f6",  # blue
            "desc": "Sama konsola bez pudełka, sprawna technicznie, normalne ślady użytkowania"
        },
        FLAWED_WORKING: {
            "label": "⚠️ Sprawny z Wadą Wizualną",
            "short_label": "Z Wadą Wiz.",
            "multiplier": 0.82,
            "badge_color": "#f59e0b",  # amber
            "desc": "Sprawna technicznie, ale widoczne pożółknięcie obudowy/ekranu lub głębokie zarysowania"
        },
        UNTESTED_JUNK: {
            "label": "🧩 Pakiet / Junk / Likwidacja",
            "short_label": "Junk / Pakiet",
            "multiplier": 0.90,
            "badge_color": "#ec4899",  # pink
            "desc": "Nietestowany pakiet hurtowy lub likwidacja szafy ze strychu (Danshari)"
        }
    }


class ConditionAnalyzer:
    """Analyzes titles, descriptions, notes, and visual cues to determine device condition."""

    @classmethod
    def detect_condition(cls, deal: Dict[str, Any]) -> Dict[str, Any]:
        title = (deal.get("title") or "").lower()
        model = (deal.get("model") or "").lower()
        note = (deal.get("custom_note") or "").lower()
        c_badge = (deal.get("condition_badge") or "").lower()
        cat_id = (deal.get("category_id") or "").lower()
        full_text = f"{title} {model} {note} {c_badge} {cat_id}"

        features: List[str] = []

        # 1. Danshari / Mystery lot / Untested Wholesale
        is_lot = any(w in full_text for w in [
            "danshari", "mystery", "karton", "pakiet", "zestaw gier", "mix",
            "まとめ", "処分", "雑多", "福袋", "引退品", "実家整理", "hurtow"
        ])
        is_untested = any(w in full_text for w in [
            "ジャンク", "未確認", "通電のみ", "junk", "nietestowan", "nieprzetestowan",
            "niesprawdzon", "ze strychu", "likwidacja"
        ])

        if is_lot or ("retro_games_mix" in cat_id) or is_untested:
            grade = ConditionGrade.UNTESTED_JUNK
            features.append("Paczka hurtowa / Danshari")
            if is_untested:
                features.append("Nietestowany (ze strychu)")
            else:
                features.append("Likwidacja kolekcji prywatnej")

        # 2. Complete in Box (CIB) / Mint Box
        elif any(w in full_text for w in [
            "完品", "元箱", "箱説", "外箱", "箱付き", "kompletny box", "w pudełku",
            "box cib", "z pudełkiem", "oryginalne pudełko", "pudełko i instrukcje", "combo"
        ]) and not any(w in full_text for w in ["goła", "sama konsola", "bez pudełka"]):
            grade = ConditionGrade.MINT_BOX
            features.append("Oryginalne pudełko (CIB)")
            if "combo" in full_text or "lcd" in full_text:
                features.append("Komplet z ekranem LCD / akcesoriami")
            else:
                features.append("Komplet kolekcjonerski")

        # 3. Flawed working / Yellowing / Scratched
        elif any(w in full_text for w in [
            "ヤケ", "液晶黄ばみ", "キズ大", "żółknięc", "pożółkł", "zżółkł",
            "głębokie rysy", "porysowan", "brak klapki", "wada wizualna"
        ]):
            grade = ConditionGrade.FLAWED_WORKING
            features.append("Sprawny 100%")
            if "żółknięc" in full_text or "ヤケ" in full_text:
                features.append("Pożółknięcie obudowy / IPS")
            else:
                features.append("Zarysowania obudowy")

        # 4. Console Only / Body Only
        elif any(w in full_text for w in [
            "本体のみ", "goła konsola", "sama konsola", "tylko konsola",
            "body only", "bez pudełka", "brak akcesoriów"
        ]):
            grade = ConditionGrade.GOOD_CONSOLE_ONLY
            features.append("Goła konsola (sprawna)")
            features.append("Brak pudełka i ładowarki")

        # 5. Default: Very Good (Sprawny, zadbany)
        else:
            grade = ConditionGrade.VERY_GOOD
            features.append("Sprawny 100% (potwierdzone)")
            features.append("Bardzo dobry stan wizualny")
            if "ips" in full_text:
                features.append("Podwójny ekran IPS")

        meta = ConditionGrade.DETAILS[grade]
        return {
            "grade": grade,
            "label": meta["label"],
            "short_label": meta["short_label"],
            "multiplier": meta["multiplier"],
            "badge_color": meta["badge_color"],
            "desc": meta["desc"],
            "features": features
        }


class AuctionClosurePredictor:
    """Predicts expected auction closing price (落札相場) and calculates market deal viability."""

    @staticmethod
    def predict_closure(
        deal: Dict[str, Any],
        rate_jpy: float = DEFAULT_JPY_PLN_RATE,
        rate_eur: float = DEFAULT_EUR_PLN_RATE
    ) -> Dict[str, Any]:
        """Calculates expected auction closure price, landed cost, and recommendation verdict."""
        # 1. Detect condition
        cond = ConditionAnalyzer.detect_condition(deal)
        grade = cond["grade"]
        multiplier = cond["multiplier"]

        current_price_jpy = float(deal.get("price_jpy", 0))
        time_rem = deal.get("time_remaining_minutes", 120)
        cat_id = deal.get("category_id", "other")
        est_pl = float(deal.get("est_pl_value", 0))

        # Base benchmark closure from deal or fallback
        base_avg = float(deal.get("closed_price_avg_jpy", current_price_jpy * 1.2))
        base_min = float(deal.get("closed_price_min_jpy", base_avg * 0.85))
        base_max = float(deal.get("closed_price_max_jpy", base_avg * 1.15))

        # Calculate condition-adjusted closing price
        predicted_closure = int(round(base_avg * multiplier // 100 * 100))
        predicted_min = int(round(base_min * multiplier // 100 * 100))
        predicted_max = int(round(base_max * multiplier // 100 * 100))

        # Auctions near end (< 60m): current bid has already advanced towards closure
        if time_rem <= 60:
            predicted_closure = max(int(current_price_jpy), min(predicted_closure, int(current_price_jpy * 1.08)))
            predicted_min = max(int(current_price_jpy), predicted_min)
            predicted_max = max(int(current_price_jpy * 1.05), predicted_max)
        else:
            predicted_closure = max(int(current_price_jpy), predicted_closure)

        # Enforce strict <= 100 PLN cap for cameras and lenses
        is_cam = is_camera_item(deal) or cat_id == "film_cameras_point_shoot"
        is_lens = is_lens_item(deal) or cat_id == "analog_lenses"
        if is_cam or is_lens:
            max_cap_pln = MAX_CAMERA_PRICE_PLN if is_cam else MAX_LENS_PRICE_PLN
            cap_jpy = int((max_cap_pln / rate_jpy) // 100 * 100)
            if current_price_jpy <= cap_jpy:
                predicted_closure = min(predicted_closure, cap_jpy)
                predicted_min = min(predicted_min, cap_jpy)
                predicted_max = min(predicted_max, cap_jpy)

        # 2. Landed cost and margin at predicted closing price
        expected_landed = calculate_landed_cost(predicted_closure, cat_id, rate_jpy, rate_eur)
        expected_landed_pln = expected_landed["landed_cost_pln"]
        expected_margin_pln = round(est_pl - expected_landed_pln, 2)
        expected_roi_pct = round((expected_margin_pln / expected_landed_pln * 100.0), 1) if expected_landed_pln > 0 else 0.0

        # Expected price jump from current bid to final closure
        closure_gap_jpy = max(0, int(predicted_closure - current_price_jpy))
        closure_gap_pct = round((closure_gap_jpy / current_price_jpy * 100.0), 1) if current_price_jpy > 0 else 0.0

        # Hard sniper cap for comparison
        target_roi = 40.0 if ("games_mix" in cat_id or est_pl <= 500) else 32.0
        cap_info = calculate_max_sniper_bid(est_pl, cat_id, target_roi, rate_jpy, rate_eur)
        max_sniper_bid = cap_info["max_bid_jpy"]
        if is_cam:
            max_sniper_bid = min(max_sniper_bid, int((MAX_CAMERA_PRICE_PLN / rate_jpy) // 100 * 100))
        if is_lens:
            max_sniper_bid = min(max_sniper_bid, int((MAX_LENS_PRICE_PLN / rate_jpy) // 100 * 100))

        # 3. Market Deal Verdict & Recommendation
        headroom_jpy = max_sniper_bid - predicted_closure

        if expected_margin_pln >= 120.0 and expected_roi_pct >= 30.0 and headroom_jpy >= 0:
            verdict_code = "S_TIER_SURE_ARBITRAGE"
            verdict_label = "🔥 S-TIER: PEWNY ARBITRAŻ"
            verdict_badge_class = "verdict-s-tier"
            rec_text = (
                f"Znakomity stan ({cond['short_label']}). Oczekiwane zamknięcie w okolicy {predicted_closure:,} JPY "
                f"(~{predicted_closure * rate_jpy:.0f} zł) zostawia aż +{expected_margin_pln:.0f} zł zysku netto w PL! "
                f"Ustaw snajpera na {max_sniper_bid:,} JPY."
            )
        elif expected_margin_pln >= 60.0 and expected_roi_pct >= 18.0 and headroom_jpy >= -600:
            verdict_code = "A_TIER_SOLID_DEAL"
            verdict_label = "⚡ A-TIER: SOLIDNA OKAZJA"
            verdict_badge_class = "verdict-a-tier"
            rec_text = (
                f"Dobra relacja ceny do stanu ({cond['short_label']}). Spodziewana cena końcowa {predicted_closure:,} JPY "
                f"daje zysk +{expected_margin_pln:.0f} zł (ROI +{expected_roi_pct:.0f}%). Warto licytować z limitem."
            )
        elif expected_margin_pln >= 25.0 and expected_roi_pct >= 10.0:
            verdict_code = "B_TIER_MARGINAL"
            verdict_label = "⚖️ B-TIER: NA STYKU OPŁACALNOŚCI"
            verdict_badge_class = "verdict-b-tier"
            rec_text = (
                f"Aukcja w cenie rynkowej ({cond['short_label']}). Oczekiwane zamknięcie {predicted_closure:,} JPY "
                f"zostawia bezpieczny bufor +{expected_margin_pln:.0f} zł. Nie przekraczaj limitu snajpera."
            )
        else:
            verdict_code = "C_TIER_OVERHEATED"
            verdict_label = "⚠️ C-TIER: RYZYKO PRZEPŁACENIA"
            verdict_badge_class = "verdict-c-tier"
            rec_text = (
                f"Licytacja może przekroczyć próg opłacalności. Oczekiwana cena zamknięcia ({predicted_closure:,} JPY) "
                f"zostawia zbyt mały margines bezpieczeństwa w Polsce ({expected_margin_pln:.0f} zł)."
            )

        return {
            "condition_grade": grade,
            "condition_label": cond["label"],
            "condition_short_label": cond["short_label"],
            "condition_badge_color": cond["badge_color"],
            "condition_features": cond["features"],
            "condition_desc": cond["desc"],
            "predicted_closure_jpy": predicted_closure,
            "predicted_closure_min_jpy": predicted_min,
            "predicted_closure_max_jpy": predicted_max,
            "predicted_closure_pln": round(predicted_closure * rate_jpy, 2),
            "closure_gap_jpy": closure_gap_jpy,
            "closure_gap_pct": closure_gap_pct,
            "expected_landed_cost_pln": expected_landed_pln,
            "expected_margin_pln": expected_margin_pln,
            "expected_roi_pct": expected_roi_pct,
            "max_sniper_bid_jpy": max_sniper_bid,
            "verdict_code": verdict_code,
            "verdict_label": verdict_label,
            "verdict_badge_class": verdict_badge_class,
            "recommendation_text": rec_text
        }
