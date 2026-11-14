"""Automated Deal Value & Worth-Buying Analyzer."""

from .config import (
    DEFAULT_JPY_PLN_RATE,
    DEFAULT_EUR_PLN_RATE,
    MAX_CAMERA_PRICE_PLN,
    MAX_LENS_PRICE_PLN
)
from .checks import (
    check_camera_price_cap,
    is_camera_item,
    check_lens_price_cap,
    is_lens_item,
    is_nintendo_ds_item
)
from .product_matcher import ProductMatcher
from .recommendation_model import RecommendationModel

class DealAnalyzer:
    """
    Evaluates deals on profitability, market liquidity, condition, 
    and logistics suitability for 60-day consolidation.
    """

    CATEGORY_WEIGHTS = {
        "nintendo_3ds_handhelds": 1.30,
        "gameboy_advance_retro": 1.25,
        "nintendo_ds_handhelds": 1.20,
        "ps_vita": 1.20,
        "ps_vita_handhelds": 1.20,
        "retro_games_mix": 1.25,
        "danshari_mystery_lots": 1.35,
        "high_margin_curated_consoles": 1.15,
        "film_cameras_point_shoot": 1.25,
        "analog_lenses": 1.15,
        "ps5_limited_controllers": 1.15,
        "ps_retro_limited_controllers": 1.10,
        "psp_handheld": 1.10,
        "nintendo_ds_consoles": 1.15,
        "nintendo_retro": 1.20,
        "psp_games_mix": 1.25,
        "ps1_consoles": 1.10,
        "retro_consoles_no_battery": 1.10,
        "ps_limited_consoles": 1.15
    }

    def __init__(self, deals, rate_jpy=DEFAULT_JPY_PLN_RATE, rate_eur=DEFAULT_EUR_PLN_RATE):
        self.deals = deals
        self.rate_jpy = float(rate_jpy)
        self.rate_eur = float(rate_eur)

    def analyze_deal(self, deal):
        """
        Calculates a 0-100 Worth-Buying Score and generates an actionable verdict.
        """
        status = deal.get("status", "Active")
        is_broken = deal.get("is_broken", False) or "Wykluczone" in status or deal.get("condition_type") == "broken"
        is_active = "Dostępne" in status and "404" not in status and "Zakończone" not in status and not is_broken

        if is_broken:
            return {
                "id": deal.get("id"),
                "score": 0,
                "tier": "EXCLUDED",
                "verdict": "WYKLUCZONE (USZKODZONE)",
                "verdict_icon": "🚫",
                "rationale": "Oferta wykluczona z listy: opis sprzedawcy wskazuje na uszkodzenie (defekt napędu/lasera/zasilania).",
                "is_active": False,
                "is_worth_buying": False
            }

        if not is_active:
            return {
                "id": deal.get("id"),
                "score": 0,
                "tier": "INACTIVE",
                "verdict": "NIEDOSTĘPNE",
                "verdict_icon": "❌",
                "rationale": "Oferta została zakończona lub wyprzedana na Mercari.",
                "is_active": False,
                "is_worth_buying": False
            }

        price_jpy = deal.get("price_jpy", 0)
        landed_cost_pln = deal.get("landed_cost_pln", 0)
        est_pl_value = deal.get("est_pl_value", 0)
        margin_pln = deal.get("est_margin_pln", 0)
        roi_percent = deal.get("roi_percent", 0)
        battery_type = deal.get("battery_type", "none")
        cat_id = deal.get("category_id", "")
        model = deal.get("model", "")
        color = deal.get("color", "")
        note = deal.get("custom_note", "")
        cond_type = deal.get("condition_type", "standard_good")
        cond_badge = deal.get("condition_badge", "✅ Stan Dobry")

        is_no_battery = battery_type != "li-ion" or "Bez Baterii" in color or "bez baterii" in note.lower()

        match_res = ProductMatcher.verify_deal(deal, deal)
        if not match_res.is_match:
            raw_price = deal.get("price_pln_raw", round(price_jpy * self.rate_jpy, 2))
            return {
                "id": deal.get("id"),
                "model": model,
                "color": color,
                "category_id": cat_id,
                "category_name": deal.get("category_name", ""),
                "price_jpy": price_jpy,
                "price_pln_raw": raw_price,
                "landed_cost_pln": landed_cost_pln,
                "est_pl_value": est_pl_value,
                "est_margin_pln": margin_pln,
                "roi_percent": roi_percent,
                "battery_type": battery_type,
                "is_no_battery": is_no_battery,
                "condition_type": cond_type,
                "condition_badge": cond_badge,
                "score": 0,
                "tier": "DISQUALIFIED",
                "verdict": "WYKLUCZONE (BŁĄD DOPASOWANIA PRODUKTU)",
                "verdict_icon": "🚫",
                "rationale": f"Niezgodność produktu: {match_res.reason}",
                "is_active": True,
                "is_worth_buying": False,
                "product_match_rejected": True,
                "product_match_reason": match_res.reason,
                "checks_passed": ["listing_sanity"],
                "checks_failed": ["product_identity_match"],
                "checks_summary": f"1 Błąd: Błędne dopasowanie ({match_res.reason})",
                "zenmarket_url": deal.get("zenmarket_url", ""),
                "mercari_url": deal.get("mercari_url", "")
            }

        if is_camera_item(deal):
            cap_ok, cap_msg = check_camera_price_cap(deal, max_price_pln=MAX_CAMERA_PRICE_PLN)
            if not cap_ok:
                raw_price = deal.get("price_pln_raw", round(price_jpy * self.rate_jpy, 2))
                return {
                    "id": deal.get("id"),
                    "model": model,
                    "color": color,
                    "category_id": cat_id,
                    "category_name": deal.get("category_name", ""),
                    "price_jpy": price_jpy,
                    "price_pln_raw": raw_price,
                    "landed_cost_pln": landed_cost_pln,
                    "est_pl_value": est_pl_value,
                    "est_margin_pln": margin_pln,
                    "roi_percent": roi_percent,
                    "battery_type": battery_type,
                    "is_no_battery": is_no_battery,
                    "condition_type": cond_type,
                    "condition_badge": cond_badge,
                    "score": 0,
                    "tier": "DISQUALIFIED",
                    "verdict": "NIE JEST OKAZJĄ (CENA APARATU > 100 ZŁ)",
                    "verdict_icon": "🚫",
                    "rationale": f"Aparat wykluczony: {cap_msg}",
                    "is_active": True,
                    "is_worth_buying": False,
                    "checks_passed": ["defects_clean", "listing_sanity"],
                    "checks_failed": ["camera_price_cap_100_pln"],
                    "checks_summary": "1 Błąd: Cena Aparatu > 100 zł (Nie Jest Okazją)",
                    "zenmarket_url": deal.get("zenmarket_url", ""),
                    "mercari_url": deal.get("mercari_url", "")
                }

        if is_lens_item(deal):
            lens_cap_ok, lens_cap_msg = check_lens_price_cap(deal, max_price_pln=MAX_LENS_PRICE_PLN)
            if not lens_cap_ok:
                raw_price = deal.get("price_pln_raw", round(price_jpy * self.rate_jpy, 2))
                return {
                    "id": deal.get("id"),
                    "model": model,
                    "color": color,
                    "category_id": cat_id,
                    "category_name": deal.get("category_name", ""),
                    "price_jpy": price_jpy,
                    "price_pln_raw": raw_price,
                    "landed_cost_pln": landed_cost_pln,
                    "est_pl_value": est_pl_value,
                    "est_margin_pln": margin_pln,
                    "roi_percent": roi_percent,
                    "battery_type": battery_type,
                    "is_no_battery": is_no_battery,
                    "condition_type": cond_type,
                    "condition_badge": cond_badge,
                    "score": 0,
                    "tier": "DISQUALIFIED",
                    "verdict": "NIE JEST OKAZJĄ (CENA OBIEKTYWU > 100 ZŁ)",
                    "verdict_icon": "🚫",
                    "rationale": f"Obiektyw wykluczony: {lens_cap_msg}",
                    "is_active": True,
                    "is_worth_buying": False,
                    "checks_passed": ["defects_clean", "listing_sanity"],
                    "checks_failed": ["lens_price_cap_100_pln"],
                    "checks_summary": "1 Błąd: Cena Obiektywu > 100 zł (Nie Jest Okazją)",
                    "zenmarket_url": deal.get("zenmarket_url", ""),
                    "mercari_url": deal.get("mercari_url", "")
                }

        margin_pts = min(35.0, max(0.0, (margin_pln / 350.0) * 35.0))

        roi_pts = min(35.0, max(0.0, (roi_percent / 70.0) * 35.0))

        is_no_battery = battery_type != "li-ion" or "Bez Baterii" in color or "bez baterii" in note.lower()
        battery_pts = 15.0 if is_no_battery else 8.0

        cat_factor = self.CATEGORY_WEIGHTS.get(cat_id, 1.0)
        liquidity_pts = min(15.0, 10.0 * cat_factor)

        opp_bonus = 0.0
        if cond_type == "untested_opportunity" and roi_percent >= 40:
            opp_bonus = 3.0

        raw_score = margin_pts + roi_pts + battery_pts + liquidity_pts + opp_bonus
        score = round(min(100.0, raw_score), 1)

        if score >= 80:
            tier = "S-TIER"
            verdict = "KUPUJ NATYCHMIAST (MUST BUY)"
            verdict_icon = "🌟"
            is_worth_buying = True
        elif score >= 65:
            tier = "A-TIER"
            verdict = "BARDZO DOBRA OKAZJA (STRONG BUY)"
            verdict_icon = "🚀"
            is_worth_buying = True
        elif score >= 50:
            tier = "B-TIER"
            verdict = "DOBRA CENA / DO KOSZYKA (FAIR DEAL)"
            verdict_icon = "🛒"
            is_worth_buying = True
        else:
            tier = "C-TIER"
            verdict = "DO ROZWAŻENIA / WATCHLISTA (WATCH)"
            verdict_icon = "⏱️"
            is_worth_buying = False

        reasons = []
        if cond_type == "untested_opportunity":
            reasons.append("⚡ sprzęt niesprawdzany przez sprzedawcę (wysoki potencjał zysku / arbitraż)")
        elif cond_type == "lens_clean":
            reasons.append("💎 optyka czysta bez defektów")
        elif cond_type == "confirmed_working":
            reasons.append("✅ sprzęt w 100% sprawdzony i przetestowany")

        if roi_percent >= 60:
            reasons.append(f"bardzo wysoki zwrot z inwestycji (+{roi_percent:.1f}% ROI)")
        elif roi_percent >= 35:
            reasons.append(f"atrakcyjna stopa zwrotu (+{roi_percent:.1f}% ROI)")

        if margin_pln >= 300:
            reasons.append(f"wysoki zysk na czysto (+{margin_pln:.0f} zł)")
        elif margin_pln >= 150:
            reasons.append(f"pewny zysk handlowy (+{margin_pln:.0f} zł)")

        if is_no_battery:
            reasons.append("brak baterii Li-Ion (0% restrykcji IATA, darmowe dopełnienie paczki)")
        else:
            reasons.append("zajmuje 1 slot bateryjny Li-Ion (maks. 2 na paczkę)")

        rationale = "Przedmiot warty zakupu: " + ", ".join(reasons) + "."

        checks_passed = ["defects_clean", "listing_sanity", "iata_battery_rule"]
        checks_failed = []
        if is_camera_item(deal):
            checks_passed.append("camera_price_cap_100_pln")
        if is_lens_item(deal):
            checks_passed.append("lens_price_cap_100_pln")
        if cond_type == "untested_opportunity":
            checks_passed.append("untested_arbitrage_gain")
        if roi_percent >= 30 and margin_pln >= 40:
            checks_passed.append("profitability_hurdle")

        checks_summary = f"{len(checks_passed)} Checków OK (0 Błędów)"

        return {
            "id": deal.get("id"),
            "model": model,
            "color": color,
            "category_id": cat_id,
            "category_name": deal.get("category_name", ""),
            "price_jpy": price_jpy,
            "price_pln_raw": deal.get("price_pln_raw", 0),
            "landed_cost_pln": landed_cost_pln,
            "est_pl_value": est_pl_value,
            "est_margin_pln": margin_pln,
            "roi_percent": roi_percent,
            "battery_type": battery_type,
            "is_no_battery": is_no_battery,
            "condition_type": cond_type,
            "condition_badge": cond_badge,
            "score": score,
            "tier": tier,
            "verdict": verdict,
            "verdict_icon": verdict_icon,
            "rationale": rationale,
            "checks_passed": checks_passed,
            "checks_failed": checks_failed,
            "checks_summary": checks_summary,
            "is_active": True,
            "is_worth_buying": is_worth_buying,
            "zenmarket_url": deal.get("zenmarket_url", ""),
            "mercari_url": deal.get("mercari_url", "")
        }

    def get_ranked_deals(self):
        """Returns active analyzed deals sorted by Worth-Buying Score descending."""
        analyzed = [self.analyze_deal(d) for d in self.deals]
        active_deals = [d for d in analyzed if d.get("is_active")]
        return sorted(active_deals, key=lambda x: x["score"], reverse=True)

    def get_optimal_consolidation_basket(self):
        """
        Constructs an optimal shipping basket complying with IATA:
        - Only genuinely qualified deals (is_worth_buying == True)
        - Exactly or up to 2 Li-Ion handhelds
        - Plus top 0% Li-Ion items (games, lenses, retro consoles)
        """
        ranked = self.get_ranked_deals()
        eligible_ranked = [d for d in ranked if d.get("is_worth_buying")]

        li_ion_items = [d for d in eligible_ranked if not d["is_no_battery"]]
        no_battery_items = [d for d in eligible_ranked if d["is_no_battery"]]

        selected_li_ion = li_ion_items[:2]
        selected_no_battery = no_battery_items[:4]

        basket = selected_li_ion + selected_no_battery
        total_jpy = sum(d["price_jpy"] for d in basket)
        total_landed_pln = sum(d["landed_cost_pln"] for d in basket)
        total_est_pln = sum(d["est_pl_value"] for d in basket)
        total_margin_pln = round(total_est_pln - total_landed_pln, 2)
        total_roi = round((total_margin_pln / total_landed_pln) * 100, 1) if total_landed_pln > 0 else 0

        return {
            "items": basket,
            "li_ion_count": len(selected_li_ion),
            "no_battery_count": len(selected_no_battery),
            "total_items": len(basket),
            "total_jpy": total_jpy,
            "total_landed_pln": round(total_landed_pln, 2),
            "total_est_pln": round(total_est_pln, 2),
            "total_margin_pln": total_margin_pln,
            "total_roi": total_roi
        }
