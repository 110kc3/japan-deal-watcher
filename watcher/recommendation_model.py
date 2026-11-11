"""Recommendation Model and Economics Engine for Polish Resale.

Implements the evidence-backed financial model defined in review/recommendation-model.md:
- Explicit separation of cash required, cash contribution before tax, and decision contribution (including owner time).
- Channel-specific selling fees (Allegro, Allegro Lokalnie, OLX).
- Multi-scenario analysis (Base, Downside -15% sale/+10% cost, Upside).
- Solved maximum bid based on hard constraints:
    * Base decision contribution >= 75 PLN
    * Cash ROI >= 25%
    * Downside decision contribution >= 0 PLN
- Removal of deceptive "guaranteed profit" or "100% win" claims.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List, Tuple


class SellingChannel(Enum):
    ALLEGRO_STANDARD = "allegro_standard"      # ~12% commission
    ALLEGRO_LOKALNIE = "allegro_lokalnie"      # 4.9% electronics, 7.9% other
    OLX_CASH = "olx_cash"                      # 0% commission, cash in hand, 10-15% haggling discount
    OLX_DELIVERY = "olx_delivery"              # 2.5% service fee paid by buyer/seller share


class RecommendationVerdict(Enum):
    BUY_UP_TO_LIMIT = "Sprawdź i kup do limitu"  # High confidence, meets all 3 criteria
    TO_VERIFY = "Do sprawdzenia"                 # Missing evidence, unknown condition or thin margin
    WATCH = "Obserwuj"                           # Price currently too high, watch for drops
    REJECTED = "Odrzucone"                       # Negative downside, mismatch, or broken unit


@dataclass
class ScenarioResult:
    scenario_name: str
    sale_proceeds_pln: float
    landed_cost_pln: float
    selling_fees_pln: float
    delivery_packing_pln: float
    return_allowance_pln: float
    cash_contribution_pln: float
    owner_time_hours: float
    owner_time_cost_pln: float
    decision_contribution_pln: float
    cash_roi_pct: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_name": self.scenario_name,
            "sale_proceeds_pln": round(self.sale_proceeds_pln, 2),
            "landed_cost_pln": round(self.landed_cost_pln, 2),
            "selling_fees_pln": round(self.selling_fees_pln, 2),
            "delivery_packing_pln": round(self.delivery_packing_pln, 2),
            "return_allowance_pln": round(self.return_allowance_pln, 2),
            "cash_contribution_pln": round(self.cash_contribution_pln, 2),
            "owner_time_hours": self.owner_time_hours,
            "owner_time_cost_pln": round(self.owner_time_cost_pln, 2),
            "decision_contribution_pln": round(self.decision_contribution_pln, 2),
            "cash_roi_pct": round(self.cash_roi_pct, 1),
        }


@dataclass
class ChannelFeeProfile:
    name: str
    channel: SellingChannel
    commission_rate: float
    fixed_fee_pln: float = 0.0
    haggling_discount_rate: float = 0.0

    @classmethod
    def get_profile(cls, channel: SellingChannel, is_electronics: bool = True) -> "ChannelFeeProfile":
        if channel == SellingChannel.ALLEGRO_STANDARD:
            return cls("Allegro Standard", channel, commission_rate=0.12, fixed_fee_pln=2.0)
        elif channel == SellingChannel.ALLEGRO_LOKALNIE:
            rate = 0.049 if is_electronics else 0.079
            return cls("Allegro Lokalnie", channel, commission_rate=rate, fixed_fee_pln=0.0)
        elif channel == SellingChannel.OLX_CASH:
            return cls("OLX Gotówka (Odbiór)", channel, commission_rate=0.0, haggling_discount_rate=0.12)
        elif channel == SellingChannel.OLX_DELIVERY:
            return cls("OLX Przesyłka", channel, commission_rate=0.02, fixed_fee_pln=0.0, haggling_discount_rate=0.08)
        return cls("Inny Kanał", channel, commission_rate=0.10)


class RecommendationModel:
    """Computes comprehensive contribution and maximum bid for Japanese imports."""

    DEFAULT_HOURLY_RATE_PLN = 60.0
    DEFAULT_HANDLING_HOURS = 0.5
    DEFAULT_DELIVERY_PACKING_PLN = 15.0
    DEFAULT_RETURN_ALLOWANCE_RATE = 0.05  # 5% reserve for defect/return allowance

    MIN_DECISION_CONTRIBUTION_PLN = 75.0
    MIN_CASH_ROI_PCT = 25.0

    @classmethod
    def evaluate_scenario(
        cls,
        sale_price_pln: float,
        landed_cost_pln: float,
        channel: SellingChannel = SellingChannel.ALLEGRO_LOKALNIE,
        is_electronics: bool = True,
        owner_hourly_rate: float = DEFAULT_HOURLY_RATE_PLN,
        handling_hours: float = DEFAULT_HANDLING_HOURS,
        delivery_packing_pln: float = DEFAULT_DELIVERY_PACKING_PLN,
        return_allowance_rate: float = DEFAULT_RETURN_ALLOWANCE_RATE,
        scenario_multiplier_sale: float = 1.0,
        scenario_multiplier_cost: float = 1.0,
        scenario_name: str = "Base"
    ) -> ScenarioResult:
        """Evaluates financial proceeds and contributions for a given scenario."""
        fee_profile = ChannelFeeProfile.get_profile(channel, is_electronics)

        # Apply haggling discount if applicable (e.g. OLX)
        effective_sale_price = sale_price_pln * (1.0 - fee_profile.haggling_discount_rate)
        # Apply scenario variance (e.g. -15% downside)
        actual_sale_proceeds = max(0.0, effective_sale_price * scenario_multiplier_sale)

        # Landed cost with scenario variance (e.g. +10% downside)
        actual_landed_cost = max(0.0, landed_cost_pln * scenario_multiplier_cost)

        # Selling fees
        selling_fees = actual_sale_proceeds * fee_profile.commission_rate + fee_profile.fixed_fee_pln
        # Return / defect reserve
        return_allowance = actual_sale_proceeds * return_allowance_rate

        # Cash contribution before income tax
        cash_contribution = actual_sale_proceeds - actual_landed_cost - selling_fees - delivery_packing_pln - return_allowance

        # Owner time cost
        owner_time_cost = handling_hours * owner_hourly_rate

        # Decision contribution
        decision_contribution = cash_contribution - owner_time_cost

        # Cash ROI % = (cash_contribution / total_cash_committed) * 100
        total_cash_committed = actual_landed_cost + delivery_packing_pln
        cash_roi_pct = (cash_contribution / total_cash_committed * 100.0) if total_cash_committed > 0 else 0.0

        return ScenarioResult(
            scenario_name=scenario_name,
            sale_proceeds_pln=actual_sale_proceeds,
            landed_cost_pln=actual_landed_cost,
            selling_fees_pln=selling_fees,
            delivery_packing_pln=delivery_packing_pln,
            return_allowance_pln=return_allowance,
            cash_contribution_pln=cash_contribution,
            owner_time_hours=handling_hours,
            owner_time_cost_pln=owner_time_cost,
            decision_contribution_pln=decision_contribution,
            cash_roi_pct=cash_roi_pct
        )

    @classmethod
    def calculate_deal_scenarios(
        cls,
        sale_price_pln: float,
        landed_cost_pln: float,
        channel: SellingChannel = SellingChannel.ALLEGRO_LOKALNIE,
        is_electronics: bool = True
    ) -> Dict[str, ScenarioResult]:
        """Calculates Base, Downside (-15% sale, +10% cost), and Upside (+10% sale) scenarios."""
        base = cls.evaluate_scenario(
            sale_price_pln=sale_price_pln,
            landed_cost_pln=landed_cost_pln,
            channel=channel,
            is_electronics=is_electronics,
            scenario_name="Base"
        )
        downside = cls.evaluate_scenario(
            sale_price_pln=sale_price_pln,
            landed_cost_pln=landed_cost_pln,
            channel=channel,
            is_electronics=is_electronics,
            scenario_multiplier_sale=0.85,  # -15% sale price
            scenario_multiplier_cost=1.10,  # +10% landed cost
            scenario_name="Downside (-15% sale / +10% cost)"
        )
        upside = cls.evaluate_scenario(
            sale_price_pln=sale_price_pln,
            landed_cost_pln=landed_cost_pln,
            channel=channel,
            is_electronics=is_electronics,
            scenario_multiplier_sale=1.10,  # +10% sale price
            scenario_multiplier_cost=1.0,
            scenario_name="Upside (+10% sale)"
        )
        return {
            "base": base,
            "downside": downside,
            "upside": upside
        }

    @classmethod
    def solve_max_bid(
        cls,
        est_sale_pln: float,
        rate_jpy: float,
        rate_eur: float,
        category_id: str = "other",
        shipping_share_pln: float = 30.0,
        channel: SellingChannel = SellingChannel.ALLEGRO_LOKALNIE,
        min_contribution_pln: float = MIN_DECISION_CONTRIBUTION_PLN,
        min_roi_pct: float = MIN_CASH_ROI_PCT,
        owner_hourly_rate: float = DEFAULT_HOURLY_RATE_PLN,
        handling_hours: float = DEFAULT_HANDLING_HOURS,
        delivery_packing_pln: float = DEFAULT_DELIVERY_PACKING_PLN,
        return_allowance_rate: float = DEFAULT_RETURN_ALLOWANCE_RATE,
        bid_increment_jpy: int = 100
    ) -> Dict[str, Any]:
        """
        Solves for the maximum purchase bid in JPY that simultaneously satisfies:
        1. Base decision contribution >= min_contribution_pln (75 PLN)
        2. Cash ROI >= min_roi_pct (25%)
        3. Downside decision contribution >= 0 PLN (nonnegative downside)
        """
        from .costs import calculate_landed_cost

        if est_sale_pln <= 0 or rate_jpy <= 0:
            return {
                "max_bid_jpy": 0,
                "is_feasible": False,
                "reason": "Nieprawidłowa wycena w Polsce lub kurs walutowy"
            }

        # Binary search for highest feasible bid in JPY
        low_jpy = 0
        # Upper bound rounded to multiple of bid_increment_jpy
        high_jpy = int((est_sale_pln / rate_jpy) * 1.5)
        high_jpy = (high_jpy // bid_increment_jpy) * bid_increment_jpy

        best_bid = -1

        for bid_test in range(high_jpy, -1, -bid_increment_jpy):
            landed = calculate_landed_cost(
                price_jpy=bid_test,
                category_id=category_id,
                rate_jpy=rate_jpy,
                rate_eur=rate_eur,
                shipping_share_pln=shipping_share_pln
            )
            scenarios = cls.calculate_deal_scenarios(
                sale_price_pln=est_sale_pln,
                landed_cost_pln=landed["landed_cost_pln"],
                channel=channel
            )
            base = scenarios["base"]
            downside = scenarios["downside"]

            # Check all 3 hard constraints
            c1 = base.decision_contribution_pln >= min_contribution_pln
            c2 = base.cash_roi_pct >= min_roi_pct
            c3 = downside.decision_contribution_pln >= 0.0

            if c1 and c2 and c3:
                best_bid = bid_test
                break

        if best_bid <= 0:
            return {
                "max_bid_jpy": 0,
                "is_feasible": False,
                "reason": "Brak opłacalnej stawki zakupu – marża lub downside nie spełniają minimalnych kryteriów (75 zł / 25% ROI / 0 zł downside)"
            }

        landed_at_best = calculate_landed_cost(best_bid, category_id, rate_jpy, rate_eur, shipping_share_pln)
        final_scenarios = cls.calculate_deal_scenarios(est_sale_pln, landed_at_best["landed_cost_pln"], channel)

        return {
            "max_bid_jpy": best_bid,
            "max_bid_pln": round(best_bid * rate_jpy, 2),
            "landed_cost_at_bid_pln": landed_at_best["landed_cost_pln"],
            "is_feasible": True,
            "base_decision_contribution_pln": final_scenarios["base"].decision_contribution_pln,
            "base_cash_roi_pct": final_scenarios["base"].cash_roi_pct,
            "downside_decision_contribution_pln": final_scenarios["downside"].decision_contribution_pln,
            "scenarios": {k: v.to_dict() for k, v in final_scenarios.items()}
        }

    @classmethod
    def determine_verdict(
        cls,
        deal: Dict[str, Any],
        scenarios: Dict[str, ScenarioResult],
        max_bid_info: Dict[str, Any]
    ) -> Tuple[RecommendationVerdict, str]:
        """
        Determines the actionable recommendation verdict:
        - Sprawdź i kup do limitu
        - Do sprawdzenia
        - Obserwuj
        - Odrzucone
        """
        is_broken = deal.get("is_broken", False)
        if is_broken:
            return RecommendationVerdict.REJECTED, "Uszkodzony sprzęt / pułapka oferty"

        # Check product match if available
        if deal.get("product_match_rejected"):
            return RecommendationVerdict.REJECTED, f"Niezgodność produktu: {deal.get('product_match_reason')}"

        if not max_bid_info.get("is_feasible", False):
            return RecommendationVerdict.REJECTED, max_bid_info.get("reason", "Brak opłacalnego limitu zakupu")

        current_price_jpy = float(deal.get("price_jpy", 0))
        max_bid_jpy = max_bid_info.get("max_bid_jpy", 0)

        # Check current price vs max bid
        if current_price_jpy > max_bid_jpy:
            return RecommendationVerdict.WATCH, f"Aktualna cena ({current_price_jpy:,} JPY) przekracza twardy limit snajpera ({max_bid_jpy:,} JPY)"

        # Check condition
        cond_type = deal.get("condition_type", "unknown")
        if cond_type in ["unknown", "cosmetic_only"]:
            return RecommendationVerdict.TO_VERIFY, "Stan techniczny niepotwierdzony – wymaga dokładnej weryfikacji opisu przed licytacją"

        base = scenarios["base"]
        downside = scenarios["downside"]

        if (
            base.decision_contribution_pln >= cls.MIN_DECISION_CONTRIBUTION_PLN
            and base.cash_roi_pct >= cls.MIN_CASH_ROI_PCT
            and downside.decision_contribution_pln >= 0.0
        ):
            return RecommendationVerdict.BUY_UP_TO_LIMIT, f"Spełnia wszystkie kryteria zakupu (wkład decyzyjny +{base.decision_contribution_pln:.0f} zł, ROI +{base.cash_roi_pct:.0f}%, twardy limit {max_bid_jpy:,} JPY)"

        return RecommendationVerdict.TO_VERIFY, "Wskaźniki opłacalności poniżej progu rekomendacji – sprawdź szczegóły"
