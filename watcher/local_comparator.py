"""Local vs. Import Sourcing Comparator (Task 9, Choice 9).

Compares Japanese landed cost + transit time (14-45 days) + cross-border import risk
versus Polish domestic buying (Allegro / OLX domestic listings in Poland).

If a product can be purchased in Poland for comparable or lower total cost
(accounting for time value of money, Polish consumer statutory 14-day return rights,
and domestic shipping), recommends "Skip Import: Kup lokalnie w Polsce".
"""

from typing import Dict, List, Any, Optional
from .config import (
    DEFAULT_JPY_PLN_RATE,
    DEFAULT_EUR_PLN_RATE
)
from .costs import calculate_landed_cost

DEFAULT_TRANSIT_DAYS_JP = 21
DEFAULT_TRANSIT_DAYS_PL = 2
DEFAULT_CAPITAL_COST_ANNUAL_RATE = 0.12
DEFAULT_IMPORT_RISK_RATE = 0.05
DEFAULT_PL_DOMESTIC_SHIPPING_PLN = 15.0

class LocalComparator:
    """
    Evaluates whether importing a given item from Japan beats buying locally in Poland.
    Incorporates full landed cost, transit time delay, capital holding cost, and consumer rights.
    """

    def __init__(
        self,
        transit_days_jp: int = DEFAULT_TRANSIT_DAYS_JP,
        transit_days_pl: int = DEFAULT_TRANSIT_DAYS_PL,
        capital_cost_annual_rate: float = DEFAULT_CAPITAL_COST_ANNUAL_RATE,
        import_risk_rate: float = DEFAULT_IMPORT_RISK_RATE,
        local_shipping_pln: float = DEFAULT_PL_DOMESTIC_SHIPPING_PLN,
        rate_jpy: float = DEFAULT_JPY_PLN_RATE,
        rate_eur: float = DEFAULT_EUR_PLN_RATE
    ):
        self.transit_days_jp = transit_days_jp
        self.transit_days_pl = transit_days_pl
        self.capital_cost_annual_rate = capital_cost_annual_rate
        self.import_risk_rate = import_risk_rate
        self.local_shipping_pln = local_shipping_pln
        self.rate_jpy = rate_jpy
        self.rate_eur = rate_eur

    def compare(
        self,
        jp_deal: Dict[str, Any],
        local_deal: Dict[str, Any],
        tolerance_pln: float = 15.0
    ) -> Dict[str, Any]:
        """
        Compares Japanese import against a Polish domestic candidate.

        Args:
            jp_deal: Japanese listing dict with price_jpy, category_id, etc.
            local_deal: Polish listing dict with price_pln, platform, shipping_pln, etc.
            tolerance_pln: If local cost is within this margin above JP landed cost,
                           recommend local buying because transit time and return rights outweigh tiny savings.
        """
        jp_price_jpy = float(jp_deal.get("price_jpy", jp_deal.get("target_price_jpy", 0)))
        category_id = jp_deal.get("category_id")
        shipping_share_pln = jp_deal.get("shipping_share_pln")

        landed_info = calculate_landed_cost(
            price_jpy=jp_price_jpy,
            category_id=category_id,
            rate_jpy=self.rate_jpy,
            rate_eur=self.rate_eur,
            shipping_share_pln=shipping_share_pln
        )
        base_jp_landed_pln = landed_info["landed_cost_pln"]

        transit_days_jp = int(jp_deal.get("transit_days", self.transit_days_jp))
        holding_cost_pln = round(
            base_jp_landed_pln * (self.capital_cost_annual_rate * (transit_days_jp / 365.0)),
            2
        )
        import_risk_pln = round(base_jp_landed_pln * self.import_risk_rate, 2)
        effective_jp_cost_pln = round(base_jp_landed_pln + holding_cost_pln + import_risk_pln, 2)

        local_price_pln = float(local_deal.get("price_pln", local_deal.get("price", 0)))
        has_smart = bool(local_deal.get("has_smart", False) or local_deal.get("free_shipping", False))
        if has_smart:
            local_shipping = 0.0
        elif "shipping_pln" in local_deal and local_deal["shipping_pln"] is not None:
            local_shipping = float(local_deal["shipping_pln"])
        else:
            local_shipping = self.local_shipping_pln

        transit_days_pl = int(local_deal.get("transit_days", self.transit_days_pl))
        effective_local_cost_pln = round(local_price_pln + local_shipping, 2)

        cost_difference_pln = round(effective_jp_cost_pln - effective_local_cost_pln, 2)
        days_saved = max(0, transit_days_jp - transit_days_pl)

        is_strictly_cheaper_local = effective_local_cost_pln <= effective_jp_cost_pln
        is_comparable_local = (effective_local_cost_pln - effective_jp_cost_pln) <= tolerance_pln

        if is_strictly_cheaper_local or is_comparable_local:
            recommendation = "skip_import"
            recommendation_label = "Skip Import: Kup lokalnie w Polsce"
            if is_strictly_cheaper_local:
                reason = (
                    f"Skip Import: Kup lokalnie w Polsce! "
                    f"Cena w Polsce ({effective_local_cost_pln:.2f} zł) jest niższa niż efektywny koszt importu z Japonii "
                    f"({effective_jp_cost_pln:.2f} zł, oszczędność: +{cost_difference_pln:.2f} zł). "
                    f"Towar masz w {transit_days_pl} dni (zamiast {transit_days_jp} dni), "
                    f"z ustawowym 14-dniowym prawem do zwrotu (UOKiK) i bez ryzyka odprawy celnej."
                )
            else:
                extra = round(effective_local_cost_pln - effective_jp_cost_pln, 2)
                reason = (
                    f"Skip Import: Kup lokalnie w Polsce! "
                    f"Różnica kosztów jest znikoma (Polska: {effective_local_cost_pln:.2f} zł vs Japonia: {effective_jp_cost_pln:.2f} zł, "
                    f"zaledwie +{extra:.2f} zł dopłaty w PL). "
                    f"Ekspresowa dostawa ({transit_days_pl} dni vs {transit_days_jp} dni) "
                    f"oraz gwarantowane prawo do zwrotu w 14 dni (UOKiK) przeważają nad importem."
                )
        else:
            recommendation = "import_japan"
            recommendation_label = "Importuj z Japonii (Arbitraż Opłacalny)"
            jp_savings = round(effective_local_cost_pln - effective_jp_cost_pln, 2)
            reason = (
                f"Importuj z Japonii: Import pozostaje wysoce opłacalny. "
                f"Efektywny koszt importu ({effective_jp_cost_pln:.2f} zł z VAT i opłatami) "
                f"jest o {jp_savings:.2f} zł niższy niż oferta w Polsce ({effective_local_cost_pln:.2f} zł)."
            )

        return {
            "recommendation": recommendation,
            "recommendation_label": recommendation_label,
            "reason": reason,
            "cost_difference_pln": cost_difference_pln,
            "days_saved": days_saved,
            "jp_sourcing": {
                "price_jpy": jp_price_jpy,
                "base_landed_cost_pln": base_jp_landed_pln,
                "holding_cost_pln": holding_cost_pln,
                "import_risk_pln": import_risk_pln,
                "effective_cost_pln": effective_jp_cost_pln,
                "transit_days": transit_days_jp,
                "return_rights": False
            },
            "local_sourcing": {
                "platform": local_deal.get("platform", "Allegro/OLX"),
                "price_pln": local_price_pln,
                "shipping_pln": local_shipping,
                "effective_cost_pln": effective_local_cost_pln,
                "transit_days": transit_days_pl,
                "return_rights": True,
                "listing_url": local_deal.get("url")
            }
        }

    def evaluate_candidates(
        self,
        jp_deal: Dict[str, Any],
        local_candidates: List[Dict[str, Any]],
        tolerance_pln: float = 15.0
    ) -> Dict[str, Any]:
        """
        Evaluates a Japanese deal against multiple Polish marketplace listings.
        Picks the best local option and produces a definitive recommendation.
        """
        if not local_candidates:
            jp_price_jpy = float(jp_deal.get("price_jpy", jp_deal.get("target_price_jpy", 0)))
            category_id = jp_deal.get("category_id")
            landed_info = calculate_landed_cost(
                price_jpy=jp_price_jpy,
                category_id=category_id,
                rate_jpy=self.rate_jpy,
                rate_eur=self.rate_eur
            )
            return {
                "recommendation": "import_japan",
                "recommendation_label": "Importuj z Japonii (Brak ofert w PL)",
                "reason": "Brak równoważnych ofert na Allegro/OLX w Polsce. Import z Japonii to jedyne źródło zaopatrzenia.",
                "cost_difference_pln": None,
                "days_saved": 0,
                "best_local_candidate": None,
                "jp_sourcing": {
                    "price_jpy": jp_price_jpy,
                    "base_landed_cost_pln": landed_info["landed_cost_pln"],
                    "effective_cost_pln": landed_info["landed_cost_pln"],
                    "transit_days": self.transit_days_jp,
                    "return_rights": False
                },
                "local_sourcing": None
            }

        comparisons = [self.compare(jp_deal, cand, tolerance_pln=tolerance_pln) for cand in local_candidates]
        best = min(comparisons, key=lambda c: c["local_sourcing"]["effective_cost_pln"])
        return best

def compare_sourcing(
    jp_deal: Dict[str, Any],
    local_deal: Dict[str, Any],
    transit_days_jp: int = DEFAULT_TRANSIT_DAYS_JP,
    transit_days_pl: int = DEFAULT_TRANSIT_DAYS_PL,
    rate_jpy: float = DEFAULT_JPY_PLN_RATE,
    rate_eur: float = DEFAULT_EUR_PLN_RATE,
    tolerance_pln: float = 15.0
) -> Dict[str, Any]:
    """Convenience helper to quickly compare a Japanese listing with a Polish domestic offer."""
    comparator = LocalComparator(
        transit_days_jp=transit_days_jp,
        transit_days_pl=transit_days_pl,
        rate_jpy=rate_jpy,
        rate_eur=rate_eur
    )
    return comparator.compare(jp_deal, local_deal, tolerance_pln=tolerance_pln)
