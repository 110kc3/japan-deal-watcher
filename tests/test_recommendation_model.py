"""Unit tests for the evidence-backed recommendation model and economics engine."""

import unittest
from watcher.recommendation_model import (
    RecommendationModel,
    SellingChannel,
    RecommendationVerdict
)


class TestRecommendationModel(unittest.TestCase):

    def test_worked_example_from_review_document(self):
        """
        Tests the worked example in review/recommendation-model.md:
        Resale 400 PLN, landed cost 240 PLN.
        Base: cash contribution 68 PLN, decision contribution 38 PLN.
        Downside (-15% sale, +10% cost): cash contribution -11.20 PLN, decision contribution -41.20 PLN.
        Previous headline gross margin was +160 PLN.
        """
        # Base scenario with specific test parameters matching the markdown doc:
        # selling fee 8%, delivery/packing + return = 60 PLN, owner time = 30 PLN (0.5h * 60)
        base = RecommendationModel.evaluate_scenario(
            sale_price_pln=400.0,
            landed_cost_pln=240.0,
            channel=SellingChannel.ALLEGRO_LOKALNIE,  # will override below
            owner_hourly_rate=60.0,
            handling_hours=0.5,
            delivery_packing_pln=35.0,  # delivery 15 + parts 20
            return_allowance_rate=0.0625,  # 25 PLN / 400 PLN = 0.0625
            scenario_name="Doc Example Base"
        )
        # Verify base contribution is much lower than naive gross margin (400 - 240 = 160)
        self.assertLess(base.decision_contribution_pln, 75.0, "Must not meet 75 PLN threshold")

        downside = RecommendationModel.evaluate_scenario(
            sale_price_pln=400.0,
            landed_cost_pln=240.0,
            channel=SellingChannel.ALLEGRO_LOKALNIE,
            owner_hourly_rate=60.0,
            handling_hours=0.5,
            delivery_packing_pln=35.0,
            return_allowance_rate=0.0625,
            scenario_multiplier_sale=0.85,
            scenario_multiplier_cost=1.10,
            scenario_name="Doc Example Downside"
        )
        # In downside, decision contribution must be negative
        self.assertLess(downside.decision_contribution_pln, 0.0)

    def test_solve_max_bid_constraints(self):
        """Tests that solve_max_bid returns a bid satisfying all 3 hard constraints."""
        rate_jpy = 0.0248
        rate_eur = 4.35
        est_sale_pln = 700.0  # high value console

        res = RecommendationModel.solve_max_bid(
            est_sale_pln=est_sale_pln,
            rate_jpy=rate_jpy,
            rate_eur=rate_eur,
            category_id="nintendo_3ds_handhelds",
            shipping_share_pln=30.0,
            channel=SellingChannel.ALLEGRO_LOKALNIE,
            min_contribution_pln=75.0,
            min_roi_pct=25.0,
            bid_increment_jpy=100
        )

        self.assertTrue(res["is_feasible"])
        self.assertGreater(res["max_bid_jpy"], 0)
        # Bid must be a multiple of 100 JPY
        self.assertEqual(res["max_bid_jpy"] % 100, 0)
        # Base decision contribution >= 75 PLN
        self.assertGreaterEqual(res["base_decision_contribution_pln"], 75.0)
        # Cash ROI >= 25%
        self.assertGreaterEqual(res["base_cash_roi_pct"], 25.0)
        # Downside contribution >= 0 PLN
        self.assertGreaterEqual(res["downside_decision_contribution_pln"], 0.0)

    def test_solve_max_bid_unfeasible_deal(self):
        """When resale value is too low to cover fixed fees and contribution, bid must be 0 and unfeasible."""
        rate_jpy = 0.0248
        rate_eur = 4.35
        est_sale_pln = 100.0  # tiny resale value cannot support 75 PLN contribution after fees

        res = RecommendationModel.solve_max_bid(
            est_sale_pln=est_sale_pln,
            rate_jpy=rate_jpy,
            rate_eur=rate_eur,
            category_id="other",
            shipping_share_pln=30.0,
            min_contribution_pln=75.0
        )

        self.assertFalse(res["is_feasible"])
        self.assertEqual(res["max_bid_jpy"], 0)

    def test_determine_verdict_rejection_of_broken(self):
        deal = {"is_broken": True, "model": "Broken PSP"}
        verdict, reason = RecommendationModel.determine_verdict(deal, {}, {})
        self.assertEqual(verdict, RecommendationVerdict.REJECTED)
        self.assertIn("Uszkodzony", reason)

    def test_determine_verdict_watch_when_over_max_bid(self):
        deal = {
            "price_jpy": 15000,
            "condition_type": "confirmed_working",
            "is_broken": False
        }
        max_bid_info = {
            "is_feasible": True,
            "max_bid_jpy": 12000
        }
        verdict, reason = RecommendationModel.determine_verdict(deal, {}, max_bid_info)
        self.assertEqual(verdict, RecommendationVerdict.WATCH)
        self.assertIn("przekracza", reason)


if __name__ == "__main__":
    unittest.main()
