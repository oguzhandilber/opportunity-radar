"""Niche-specific scoring for opportunities.

Scores opportunities within their detected niche using niche-specific benchmarks.
Calculates niche fit score and niche opportunity score.
"""

from dataclasses import dataclass
from typing import Dict, Optional

from app.analyzers.niche_database import get_niche
from app.analyzers.niche_detector import NicheDetectionResult


@dataclass
class NicheScoreResult:
    """Result of niche-specific scoring."""

    niche_id: str
    niche_name: str
    niche_fit_score: float  # 0-10: How well opportunity fits the niche
    niche_opportunity_score: float  # 0-10: How good the opportunity is for this niche
    overall_niche_score: float  # 0-10: Combined score
    market_attractiveness: float  # 0-10: Based on market size and growth
    competitive_landscape: str  # "low", "medium", "high" competition
    benchmark_comparison: Dict[str, float]  # Comparison to niche benchmarks
    recommendations: list[str]  # Niche-specific recommendations


class NicheScorer:
    """Scores opportunities within their detected niche.

    Provides niche-specific scoring that considers:
    - How well the opportunity fits the niche (niche fit)
    - How good the opportunity is within that niche (niche quality)
    - Market size and growth potential
    - Competitive landscape
    """

    def __init__(self):
        """Initialize niche scorer."""
        pass

    def score(
        self,
        niche_detection: NicheDetectionResult,
        opportunity_data: Dict,
        primary_only: bool = False
    ) -> Dict[str, NicheScoreResult]:
        """Score opportunity for detected niche(s).

        Args:
            niche_detection: Result from NicheDetector
            opportunity_data: Dictionary with opportunity fields
            primary_only: If True, only score the primary niche

        Returns:
            Dictionary mapping niche_id to NicheScoreResult
        """
        if not niche_detection.matches:
            return {}

        scores = {}

        # Score primary niche
        if niche_detection.primary_niche:
            primary_score = self._score_for_niche(
                niche_detection.primary_niche.niche_id,
                niche_detection.primary_niche.confidence,
                opportunity_data,
                is_primary=True
            )
            scores[niche_detection.primary_niche.niche_id] = primary_score

        # Score secondary niches if requested
        if not primary_only and niche_detection.is_multi_niche:
            for match in niche_detection.matches[1:4]:  # Up to 3 secondary niches
                if match.confidence >= 0.25:  # Only score significant secondary matches
                    secondary_score = self._score_for_niche(
                        match.niche_id,
                        match.confidence,
                        opportunity_data,
                        is_primary=False
                    )
                    scores[match.niche_id] = secondary_score

        return scores

    def _score_for_niche(
        self,
        niche_id: str,
        detection_confidence: float,
        opportunity_data: Dict,
        is_primary: bool
    ) -> NicheScoreResult:
        """Score opportunity for a specific niche.

        Args:
            niche_id: ID of the niche
            detection_confidence: Confidence from niche detection
            opportunity_data: Opportunity data dictionary
            is_primary: Whether this is the primary niche

        Returns:
            NicheScoreResult
        """
        niche = get_niche(niche_id)
        if not niche:
            # Fallback for unknown niche
            return NicheScoreResult(
                niche_id=niche_id,
                niche_name="Unknown",
                niche_fit_score=0.0,
                niche_opportunity_score=0.0,
                overall_niche_score=0.0,
                market_attractiveness=5.0,
                competitive_landscape="medium",
                benchmark_comparison={},
                recommendations=[]
            )

        # 1. Calculate niche fit score (how well it fits this niche)
        niche_fit_score = self._calculate_fit_score(
            niche,
            detection_confidence,
            opportunity_data
        )

        # 2. Calculate niche opportunity score (how good the opportunity is for this niche)
        niche_opportunity_score = self._calculate_opportunity_score(
            niche,
            opportunity_data
        )

        # 3. Calculate market attractiveness
        market_attractiveness = self._calculate_market_attractiveness(niche)

        # 4. Determine competitive landscape
        competitive_landscape = self._assess_competition(niche, opportunity_data)

        # 5. Benchmark comparison
        benchmark_comparison = self._compare_to_benchmarks(
            niche,
            opportunity_data
        )

        # 6. Calculate overall niche score
        # Weighted combination: fit (30%), opportunity (40%), market (30%)
        overall_score = (
            niche_fit_score * 0.3 +
            niche_opportunity_score * 0.4 +
            market_attractiveness * 0.3
        )

        # 7. Generate niche-specific recommendations
        recommendations = self._generate_recommendations(
            niche,
            niche_fit_score,
            niche_opportunity_score,
            competitive_landscape,
            opportunity_data
        )

        return NicheScoreResult(
            niche_id=niche_id,
            niche_name=niche.name,
            niche_fit_score=round(niche_fit_score, 2),
            niche_opportunity_score=round(niche_opportunity_score, 2),
            overall_niche_score=round(overall_score, 2),
            market_attractiveness=round(market_attractiveness, 2),
            competitive_landscape=competitive_landscape,
            benchmark_comparison=benchmark_comparison,
            recommendations=recommendations
        )

    def _calculate_fit_score(
        self,
        niche,
        detection_confidence: float,
        opportunity_data: Dict
    ) -> float:
        """Calculate how well the opportunity fits the niche (0-10).

        Args:
            niche: NicheDefinition
            detection_confidence: Confidence from detection (0-1)
            opportunity_data: Opportunity data

        Returns:
            Fit score from 0-10
        """
        # Base score from detection confidence
        base_score = detection_confidence * 10

        # Bonus for business model alignment
        business_model = opportunity_data.get("business_model", "").lower()
        if business_model:
            common_models = [m.lower() for m in niche.common_business_models]
            if any(model in business_model for model in common_models):
                base_score += 1.0

        # Bonus for sector alignment
        sector = opportunity_data.get("sector", "").lower()
        if sector and (sector in niche.name.lower() or niche.name.lower() in sector):
            base_score += 1.0

        return min(10.0, base_score)

    def _calculate_opportunity_score(
        self,
        niche,
        opportunity_data: Dict
    ) -> float:
        """Calculate how good the opportunity is within this niche (0-10).

        Args:
            niche: NicheDefinition
            opportunity_data: Opportunity data

        Returns:
            Opportunity score from 0-10
        """
        # Start with base scores
        demand = opportunity_data.get("demand_score", 5.0)
        market = opportunity_data.get("market_score", 5.0)
        revenue = opportunity_data.get("revenue_score", 5.0)

        # Base opportunity score: weighted average
        base_score = (demand * 0.4 + market * 0.3 + revenue * 0.3)

        # Adjust based on niche-specific factors

        # Payment signals are more important in B2B niches
        b2b_niches = ["devtools", "saas", "hr_tech", "legal_tech", "sales_tech", "martech", "security"]
        if niche.id in b2b_niches:
            payment_tier = opportunity_data.get("payment_signal_tier")
            if payment_tier and payment_tier <= 2:
                base_score += 1.0  # Bonus for strong payment signals in B2B

        # Consumer niches value high engagement
        b2c_niches = ["healthtech", "edtech", "foodtech", "productivity", "creator_economy"]
        if niche.id in b2c_niches:
            # Placeholder: would check engagement metrics
            # For now, bonus if revenue_potential is high
            revenue_potential = opportunity_data.get("revenue_potential_score", 0)
            if revenue_potential >= 7:
                base_score += 0.5

        # High-growth niches get bonus for innovation
        if niche.growth_rate >= 20:
            feasibility = opportunity_data.get("feasibility_score", 5.0)
            if feasibility >= 7:  # Feasible innovation is valuable
                base_score += 0.5

        return min(10.0, base_score)

    def _calculate_market_attractiveness(self, niche) -> float:
        """Calculate market attractiveness score (0-10).

        Args:
            niche: NicheDefinition

        Returns:
            Attractiveness score from 0-10
        """
        # Base on market size and growth rate
        # Market size score (0-5): logarithmic scale
        import math
        market_score = min(5.0, math.log10(max(1, niche.market_size_billions)) * 1.5)

        # Growth rate score (0-5): linear with cap
        growth_score = min(5.0, niche.growth_rate / 8.0)

        return market_score + growth_score

    def _assess_competition(self, niche, opportunity_data: Dict) -> str:
        """Assess competitive landscape.

        Args:
            niche: NicheDefinition
            opportunity_data: Opportunity data

        Returns:
            "low", "medium", or "high" competition
        """
        # Large markets with many successful examples = high competition
        successful_count = len(niche.successful_examples)

        # Check if competitors are mentioned
        competitors = opportunity_data.get("competitors", [])
        mentioned_competitors = len(competitors) if competitors else 0

        # Scoring logic
        score = 0

        if successful_count >= 8:
            score += 2
        elif successful_count >= 5:
            score += 1

        if mentioned_competitors >= 3:
            score += 2
        elif mentioned_competitors >= 1:
            score += 1

        # Market size also indicates competition
        if niche.market_size_billions >= 100:
            score += 1

        if score >= 4:
            return "high"
        elif score >= 2:
            return "medium"
        else:
            return "low"

    def _compare_to_benchmarks(
        self,
        niche,
        opportunity_data: Dict
    ) -> Dict[str, float]:
        """Compare opportunity to niche benchmarks.

        Args:
            niche: NicheDefinition
            opportunity_data: Opportunity data

        Returns:
            Dictionary of benchmark comparisons
        """
        benchmarks = {}

        # Compare deal size (if B2B)
        if niche.avg_deal_size:
            estimated_deal = opportunity_data.get("monthly_price_estimate", 0)
            if estimated_deal:
                annual_deal = estimated_deal * 12
                ratio = annual_deal / niche.avg_deal_size if niche.avg_deal_size else 0
                benchmarks["deal_size_vs_avg"] = round(ratio, 2)

        # Compare to growth rate
        benchmarks["market_growth_rate"] = niche.growth_rate

        # Success pattern match (if available)
        success_prediction = opportunity_data.get("success_prediction")
        if success_prediction:
            benchmarks["success_likelihood"] = success_prediction

        return benchmarks

    def _generate_recommendations(
        self,
        niche,
        fit_score: float,
        opportunity_score: float,
        competitive_landscape: str,
        opportunity_data: Dict
    ) -> list[str]:
        """Generate niche-specific recommendations.

        Args:
            niche: NicheDefinition
            fit_score: Niche fit score
            opportunity_score: Niche opportunity score
            competitive_landscape: Competition level
            opportunity_data: Opportunity data

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Fit-based recommendations
        if fit_score < 6:
            recommendations.append(
                f"Strengthen positioning in {niche.name} by addressing key pain points"
            )
        elif fit_score >= 8:
            recommendations.append(
                f"Strong fit for {niche.name} - emphasize this in marketing"
            )

        # Competition-based recommendations
        if competitive_landscape == "high":
            recommendations.append(
                "High competition - focus on unique differentiation and niche positioning"
            )
            if niche.successful_examples:
                recommendations.append(
                    f"Study successful players: {', '.join(niche.successful_examples[:3])}"
                )
        elif competitive_landscape == "low":
            recommendations.append(
                "Low competition detected - opportunity for market leadership"
            )

        # Growth-based recommendations
        if niche.growth_rate >= 20:
            recommendations.append(
                f"High-growth market ({niche.growth_rate}% annually) - move quickly to capture share"
            )

        # Business model recommendations
        business_model = opportunity_data.get("business_model", "")
        if business_model and business_model not in niche.common_business_models:
            recommendations.append(
                f"Consider {niche.common_business_models[0]} model - common in {niche.name}"
            )

        # Target customer recommendations
        if niche.target_customers:
            recommendations.append(
                f"Target customers: {', '.join(niche.target_customers[:3])}"
            )

        # Limit to top 5 recommendations
        return recommendations[:5]
