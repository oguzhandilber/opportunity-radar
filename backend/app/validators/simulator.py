"""Validation simulator for opportunity validation.

Simulates validation results based on opportunity quality and characteristics.
This is useful for estimating potential outcomes before running real experiments.
"""

import random
from dataclasses import dataclass
from typing import Optional

from app.validators.toolkit import ValidationToolType


@dataclass
class SimulationResult:
    """Simulated validation result."""
    tool_type: ValidationToolType
    metrics: dict[str, float]
    confidence: float  # 0-1 confidence in simulation
    assumptions: list[str]  # What assumptions were made
    notes: str


class ValidationSimulator:
    """Simulates validation results based on opportunity characteristics.

    Uses opportunity quality signals (payment intent, success prediction, etc.)
    to estimate realistic validation outcomes.
    """

    def simulate_landing_page(
        self,
        payment_intent: Optional[float] = None,
        success_prediction: Optional[float] = None,
        niche_fit: Optional[float] = None,
        traffic_volume: int = 1000
    ) -> SimulationResult:
        """Simulate landing page performance.

        Args:
            payment_intent: 0-1 payment intent score
            success_prediction: 0-100 success prediction
            niche_fit: 0-10 how well opportunity fits a niche
            traffic_volume: Expected number of visitors

        Returns:
            Simulated landing page metrics
        """
        # Default values if not provided
        payment_intent = payment_intent or 0.5
        success_prediction = success_prediction or 50
        niche_fit = niche_fit or 5

        # Base conversion rate (influenced by opportunity quality)
        quality_factor = (
            (payment_intent * 0.4) +
            (success_prediction / 100 * 0.4) +
            (niche_fit / 10 * 0.2)
        )

        # Base conversion rate: 0.5% to 5% based on quality
        base_conversion = 0.005 + (quality_factor * 0.045)

        # Add realistic variance (+/- 30%)
        variance = random.uniform(-0.3, 0.3)
        conversion_rate = max(0.001, base_conversion * (1 + variance))

        # Calculate derived metrics
        signups = int(traffic_volume * conversion_rate)
        bounce_rate = max(0.2, min(0.9, 0.7 - (quality_factor * 0.3)))
        avg_time_on_page = 30 + (quality_factor * 90)  # 30-120 seconds

        assumptions = [
            f"Traffic volume: {traffic_volume} visitors",
            f"Quality factor: {quality_factor:.2f}",
            "Conversion rate varies by messaging quality",
            "Traffic source affects bounce rate"
        ]

        return SimulationResult(
            tool_type=ValidationToolType.LANDING_PAGE,
            metrics={
                "visitors": traffic_volume,
                "signups": signups,
                "conversion_rate": round(conversion_rate * 100, 2),
                "bounce_rate": round(bounce_rate * 100, 2),
                "avg_time_on_page_seconds": round(avg_time_on_page, 1)
            },
            confidence=0.6,  # Moderate confidence in simulation
            assumptions=assumptions,
            notes=f"Simulated based on quality factor {quality_factor:.2f}"
        )

    def simulate_ad_campaign(
        self,
        payment_intent: Optional[float] = None,
        success_prediction: Optional[float] = None,
        budget: float = 500,
        platform: str = "google"
    ) -> SimulationResult:
        """Simulate ad campaign performance.

        Args:
            payment_intent: 0-1 payment intent score
            success_prediction: 0-100 success prediction
            budget: Ad budget in USD
            platform: Ad platform (google, facebook, linkedin)

        Returns:
            Simulated ad campaign metrics
        """
        payment_intent = payment_intent or 0.5
        success_prediction = success_prediction or 50

        quality_factor = (payment_intent * 0.5) + (success_prediction / 100 * 0.5)

        # Platform-specific base CTR and CPC
        platform_params = {
            "google": {"base_ctr": 0.02, "base_cpc": 2.0},
            "facebook": {"base_ctr": 0.015, "base_cpc": 1.5},
            "linkedin": {"base_ctr": 0.01, "base_cpc": 5.0}
        }

        params = platform_params.get(platform.lower(), platform_params["google"])

        # CTR influenced by quality
        ctr = params["base_ctr"] * (0.5 + quality_factor)
        ctr = ctr * random.uniform(0.7, 1.3)  # Add variance

        # CPC with variance
        cpc = params["base_cpc"] * random.uniform(0.8, 1.2)

        # Calculate metrics
        clicks = int(budget / cpc)
        impressions = int(clicks / ctr) if ctr > 0 else 0
        conversions = int(clicks * (0.02 + quality_factor * 0.08))
        cpa = budget / conversions if conversions > 0 else 0

        assumptions = [
            f"Platform: {platform}",
            f"Budget: ${budget}",
            "CTR varies by ad creative quality",
            "CPC fluctuates based on competition"
        ]

        return SimulationResult(
            tool_type=ValidationToolType.AD_CAMPAIGN,
            metrics={
                "impressions": impressions,
                "clicks": clicks,
                "ctr": round(ctr * 100, 2),
                "cpc": round(cpc, 2),
                "conversions": conversions,
                "cpa": round(cpa, 2) if cpa > 0 else 0,
                "budget_spent": budget
            },
            confidence=0.5,
            assumptions=assumptions,
            notes=f"Simulated {platform} campaign with quality factor {quality_factor:.2f}"
        )

    def simulate_email_list(
        self,
        payment_intent: Optional[float] = None,
        success_prediction: Optional[float] = None,
        promotion_reach: int = 5000
    ) -> SimulationResult:
        """Simulate email list building performance.

        Args:
            payment_intent: 0-1 payment intent score
            success_prediction: 0-100 success prediction
            promotion_reach: How many people see the lead magnet promotion

        Returns:
            Simulated email list metrics
        """
        payment_intent = payment_intent or 0.5
        success_prediction = success_prediction or 50

        quality_factor = (payment_intent * 0.5) + (success_prediction / 100 * 0.5)

        # Signup rate: 1% to 10% based on lead magnet quality
        signup_rate = 0.01 + (quality_factor * 0.09)
        signup_rate = signup_rate * random.uniform(0.7, 1.3)

        subscribers = int(promotion_reach * signup_rate)

        # Email engagement metrics
        open_rate = 0.15 + (quality_factor * 0.25)  # 15-40%
        click_rate = 0.02 + (quality_factor * 0.08)  # 2-10%

        assumptions = [
            f"Promotion reach: {promotion_reach} people",
            "Lead magnet quality affects signup rate",
            "List quality affects engagement rates"
        ]

        return SimulationResult(
            tool_type=ValidationToolType.EMAIL_LIST,
            metrics={
                "reach": promotion_reach,
                "subscribers": subscribers,
                "signup_rate": round(signup_rate * 100, 2),
                "est_open_rate": round(open_rate * 100, 2),
                "est_click_rate": round(click_rate * 100, 2)
            },
            confidence=0.65,
            assumptions=assumptions,
            notes=f"Simulated based on quality factor {quality_factor:.2f}"
        )

    def simulate_survey(
        self,
        payment_intent: Optional[float] = None,
        target_responses: int = 100,
        distribution_size: int = 500
    ) -> SimulationResult:
        """Simulate survey performance.

        Args:
            payment_intent: 0-1 payment intent score
            target_responses: Desired number of responses
            distribution_size: How many people receive survey

        Returns:
            Simulated survey metrics
        """
        payment_intent = payment_intent or 0.5

        # Response rate: 10-30% based on audience engagement
        base_response_rate = 0.10 + (payment_intent * 0.20)
        response_rate = base_response_rate * random.uniform(0.8, 1.2)

        responses = min(int(distribution_size * response_rate), target_responses)
        completion_rate = 0.60 + (payment_intent * 0.25)  # 60-85%

        # Pain point intensity (1-10 scale)
        avg_pain_intensity = 4 + (payment_intent * 4)  # 4-8

        # Willingness to pay (percentage who would pay)
        willingness_to_pay = 0.20 + (payment_intent * 0.50)  # 20-70%

        assumptions = [
            f"Survey distributed to {distribution_size} people",
            "Response rate depends on audience relevance",
            "Completion rate varies by survey length"
        ]

        return SimulationResult(
            tool_type=ValidationToolType.SURVEY,
            metrics={
                "distributed": distribution_size,
                "responses": responses,
                "response_rate": round(response_rate * 100, 2),
                "completion_rate": round(completion_rate * 100, 2),
                "avg_pain_intensity": round(avg_pain_intensity, 1),
                "willingness_to_pay_pct": round(willingness_to_pay * 100, 2)
            },
            confidence=0.7,
            assumptions=assumptions,
            notes=f"Simulated with payment intent {payment_intent:.2f}"
        )

    def simulate_mvp(
        self,
        payment_intent: Optional[float] = None,
        success_prediction: Optional[float] = None,
        niche_fit: Optional[float] = None,
        initial_users: int = 100
    ) -> SimulationResult:
        """Simulate MVP performance.

        Args:
            payment_intent: 0-1 payment intent score
            success_prediction: 0-100 success prediction
            niche_fit: 0-10 niche fit score
            initial_users: Number of initial users

        Returns:
            Simulated MVP metrics
        """
        payment_intent = payment_intent or 0.5
        success_prediction = success_prediction or 50
        niche_fit = niche_fit or 5

        quality_factor = (
            (payment_intent * 0.35) +
            (success_prediction / 100 * 0.35) +
            (niche_fit / 10 * 0.30)
        )

        # Retention rates
        day1_retention = 0.30 + (quality_factor * 0.40)  # 30-70%
        day7_retention = day1_retention * (0.40 + quality_factor * 0.30)  # 40-70% of day 1
        day30_retention = day7_retention * (0.50 + quality_factor * 0.30)  # 50-80% of day 7

        # Conversion to paid
        conversion_to_paid = 0.02 + (payment_intent * 0.18)  # 2-20%

        active_users = int(initial_users * day1_retention)
        paid_users = int(initial_users * conversion_to_paid)

        assumptions = [
            f"Initial users: {initial_users}",
            "Retention depends on product-market fit",
            "Conversion depends on value delivery",
            "Quality factor incorporates multiple signals"
        ]

        return SimulationResult(
            tool_type=ValidationToolType.MVP,
            metrics={
                "initial_users": initial_users,
                "day1_retention": round(day1_retention * 100, 2),
                "day7_retention": round(day7_retention * 100, 2),
                "day30_retention": round(day30_retention * 100, 2),
                "active_users": active_users,
                "paid_users": paid_users,
                "conversion_to_paid": round(conversion_to_paid * 100, 2)
            },
            confidence=0.5,
            assumptions=assumptions,
            notes=f"Simulated MVP with quality factor {quality_factor:.2f}"
        )

    def simulate(
        self,
        tool_type: ValidationToolType,
        payment_intent: Optional[float] = None,
        success_prediction: Optional[float] = None,
        niche_fit: Optional[float] = None,
        config: Optional[dict] = None
    ) -> SimulationResult:
        """Simulate validation for any tool type.

        Args:
            tool_type: Type of validation tool
            payment_intent: 0-1 payment intent score
            success_prediction: 0-100 success prediction
            niche_fit: 0-10 niche fit score
            config: Tool-specific configuration

        Returns:
            Simulated validation result
        """
        config = config or {}

        if tool_type == ValidationToolType.LANDING_PAGE:
            return self.simulate_landing_page(
                payment_intent=payment_intent,
                success_prediction=success_prediction,
                niche_fit=niche_fit,
                traffic_volume=config.get("traffic_volume", 1000)
            )
        elif tool_type == ValidationToolType.AD_CAMPAIGN:
            return self.simulate_ad_campaign(
                payment_intent=payment_intent,
                success_prediction=success_prediction,
                budget=config.get("budget", 500),
                platform=config.get("platform", "google")
            )
        elif tool_type == ValidationToolType.EMAIL_LIST:
            return self.simulate_email_list(
                payment_intent=payment_intent,
                success_prediction=success_prediction,
                promotion_reach=config.get("promotion_reach", 5000)
            )
        elif tool_type == ValidationToolType.SURVEY:
            return self.simulate_survey(
                payment_intent=payment_intent,
                target_responses=config.get("target_responses", 100),
                distribution_size=config.get("distribution_size", 500)
            )
        elif tool_type == ValidationToolType.MVP:
            return self.simulate_mvp(
                payment_intent=payment_intent,
                success_prediction=success_prediction,
                niche_fit=niche_fit,
                initial_users=config.get("initial_users", 100)
            )
        else:
            # For other tool types, return a basic simulation
            return SimulationResult(
                tool_type=tool_type,
                metrics={},
                confidence=0.3,
                assumptions=["Basic simulation - limited data available"],
                notes=f"Tool type {tool_type} not fully supported yet"
            )
