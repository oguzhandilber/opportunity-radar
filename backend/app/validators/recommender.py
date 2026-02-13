"""Validation recommender for opportunity validation.

Recommends the best validation approach for each opportunity based on
budget, time, and risk tolerance.
"""

from dataclasses import dataclass
from typing import Optional

from app.validators.toolkit import ValidationToolkit, ValidationTool, ValidationToolType


@dataclass
class ValidationStep:
    """A recommended validation step."""
    tool: ValidationTool
    priority: int  # 1 = highest priority
    reasoning: str
    expected_outcome: str
    risk_mitigation: str


@dataclass
class ValidationPlan:
    """A complete validation plan for an opportunity."""
    steps: list[ValidationStep]
    total_cost_min: float
    total_cost_max: float
    total_time_days: int
    confidence_level: str  # "low", "medium", "high"
    overall_strategy: str


class ValidationRecommender:
    """Recommends validation strategies for opportunities."""

    def __init__(self):
        """Initialize recommender."""
        self.toolkit = ValidationToolkit()

    def recommend(
        self,
        budget: str = "medium",  # "low", "medium", "high"
        time_available: str = "medium",  # "short", "medium", "long"
        risk_tolerance: str = "medium",  # "low", "medium", "high"
        payment_intent: Optional[float] = None,
        success_prediction: Optional[float] = None,
        product_type: Optional[str] = None
    ) -> ValidationPlan:
        """Recommend validation approach for an opportunity.

        Args:
            budget: Budget level (low=$0-300, medium=$300-2000, high=$2000+)
            time_available: Time available (short=<7days, medium=7-30days, long=>30days)
            risk_tolerance: Risk tolerance (low=safe, medium=balanced, high=aggressive)
            payment_intent: 0-1 payment intent score
            success_prediction: 0-100 success prediction
            product_type: Type of product (SaaS, Mobile App, etc.)

        Returns:
            ValidationPlan with recommended steps
        """
        # Convert budget levels to dollar amounts
        budget_limits = {
            "low": 300,
            "medium": 2000,
            "high": 10000
        }

        time_limits = {
            "short": 7,
            "medium": 30,
            "long": 90
        }

        max_budget = budget_limits.get(budget, 2000)
        max_days = time_limits.get(time_available, 30)

        # Get filtered tools
        available_tools = self.toolkit.get_tools_by_budget(max_budget)
        available_tools = [t for t in available_tools if t.time_estimate_days <= max_days]

        if not available_tools:
            # Fallback to cheapest/fastest options
            all_tools = self.toolkit.get_all_tools()
            available_tools = sorted(all_tools, key=lambda t: (t.cost_estimate_min, t.time_estimate_days))[:3]

        # Score and prioritize tools
        scored_tools = self._score_tools(
            available_tools,
            payment_intent or 0.5,
            success_prediction or 50,
            risk_tolerance,
            product_type
        )

        # Build validation plan
        steps = self._build_steps(scored_tools, risk_tolerance)

        # Calculate totals
        total_cost_min = sum(step.tool.cost_estimate_min for step in steps)
        total_cost_max = sum(step.tool.cost_estimate_max for step in steps)
        total_time_days = max(step.tool.time_estimate_days for step in steps) if steps else 0

        # Determine confidence level
        confidence = self._calculate_confidence(steps, payment_intent or 0.5)

        # Generate overall strategy
        strategy = self._generate_strategy(steps, budget, time_available, risk_tolerance)

        return ValidationPlan(
            steps=steps,
            total_cost_min=total_cost_min,
            total_cost_max=total_cost_max,
            total_time_days=total_time_days,
            confidence_level=confidence,
            overall_strategy=strategy
        )

    def _score_tools(
        self,
        tools: list[ValidationTool],
        payment_intent: float,
        success_prediction: float,
        risk_tolerance: str,
        product_type: Optional[str]
    ) -> list[tuple[ValidationTool, float]]:
        """Score tools based on opportunity characteristics."""
        scored = []

        for tool in tools:
            score = 0.0

            # High payment intent favors paid validation (ads, MVP)
            if payment_intent > 0.6:
                if tool.tool_type in [ValidationToolType.AD_CAMPAIGN, ValidationToolType.MVP]:
                    score += 2.0
                elif tool.tool_type == ValidationToolType.LANDING_PAGE:
                    score += 1.5

            # Low payment intent favors cheap validation (social, survey)
            if payment_intent < 0.4:
                if tool.tool_type in [ValidationToolType.SOCIAL_POST, ValidationToolType.SURVEY]:
                    score += 2.0

            # High success prediction favors deeper validation
            if success_prediction > 60:
                if tool.tool_type in [ValidationToolType.MVP, ValidationToolType.WAITLIST]:
                    score += 1.5

            # Risk tolerance affects tool selection
            if risk_tolerance == "low":
                # Prefer cheap, fast validation
                if tool.difficulty == "easy":
                    score += 1.5
                if tool.cost_estimate_max < 200:
                    score += 1.0
            elif risk_tolerance == "high":
                # Willing to invest more
                if tool.tool_type in [ValidationToolType.MVP, ValidationToolType.AD_CAMPAIGN]:
                    score += 2.0

            # Product type specific recommendations
            if product_type:
                if "SaaS" in product_type or "B2B" in product_type:
                    if tool.tool_type in [ValidationToolType.COLD_OUTREACH, ValidationToolType.LANDING_PAGE]:
                        score += 1.0
                if "Mobile" in product_type or "App" in product_type:
                    if tool.tool_type in [ValidationToolType.LANDING_PAGE, ValidationToolType.WAITLIST]:
                        score += 1.0

            # Baseline score for all tools
            score += 1.0

            scored.append((tool, score))

        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    def _build_steps(
        self,
        scored_tools: list[tuple[ValidationTool, float]],
        risk_tolerance: str
    ) -> list[ValidationStep]:
        """Build validation steps from scored tools."""
        steps = []

        # Number of steps based on risk tolerance
        num_steps = {
            "low": 2,      # Quick validation
            "medium": 3,   # Balanced approach
            "high": 4      # Thorough validation
        }.get(risk_tolerance, 3)

        # Take top N tools
        priority = 1
        for tool, score in scored_tools[:num_steps]:
            reasoning = self._generate_reasoning(tool, score)
            expected_outcome = self._generate_expected_outcome(tool)
            risk_mitigation = self._generate_risk_mitigation(tool)

            steps.append(ValidationStep(
                tool=tool,
                priority=priority,
                reasoning=reasoning,
                expected_outcome=expected_outcome,
                risk_mitigation=risk_mitigation
            ))
            priority += 1

        return steps

    def _generate_reasoning(self, tool: ValidationTool, score: float) -> str:
        """Generate reasoning for why this tool was selected."""
        if tool.tool_type == ValidationToolType.LANDING_PAGE:
            return "Landing page tests are ideal for quickly measuring interest with minimal cost"
        elif tool.tool_type == ValidationToolType.AD_CAMPAIGN:
            return "Paid ads provide fast feedback on messaging and market size"
        elif tool.tool_type == ValidationToolType.EMAIL_LIST:
            return "Building an email list allows direct communication with interested users"
        elif tool.tool_type == ValidationToolType.SURVEY:
            return "Surveys help understand pain points and feature priorities"
        elif tool.tool_type == ValidationToolType.MVP:
            return "An MVP validates actual usage and willingness to pay"
        elif tool.tool_type == ValidationToolType.SOCIAL_POST:
            return "Social media posts are the fastest way to gauge initial interest"
        elif tool.tool_type == ValidationToolType.COLD_OUTREACH:
            return "Direct outreach provides qualitative feedback from potential customers"
        elif tool.tool_type == ValidationToolType.WAITLIST:
            return "Waitlists measure commitment and build anticipation"
        return f"This tool scored {score:.1f} based on opportunity characteristics"

    def _generate_expected_outcome(self, tool: ValidationTool) -> str:
        """Generate expected outcome description."""
        if tool.tool_type == ValidationToolType.LANDING_PAGE:
            return "2-5% conversion rate for strong product-market fit"
        elif tool.tool_type == ValidationToolType.AD_CAMPAIGN:
            return "1-3% CTR and clear understanding of customer acquisition cost"
        elif tool.tool_type == ValidationToolType.EMAIL_LIST:
            return "100-500 interested subscribers for validation"
        elif tool.tool_type == ValidationToolType.SURVEY:
            return "Quantitative data on pain points and pricing"
        elif tool.tool_type == ValidationToolType.MVP:
            return "20-40% day 7 retention for strong product"
        elif tool.tool_type == ValidationToolType.SOCIAL_POST:
            return "50-200 engaged users showing interest"
        elif tool.tool_type == ValidationToolType.COLD_OUTREACH:
            return "10-20% positive response rate"
        elif tool.tool_type == ValidationToolType.WAITLIST:
            return "100+ committed signups"
        return "Measurable validation data"

    def _generate_risk_mitigation(self, tool: ValidationTool) -> str:
        """Generate risk mitigation strategy."""
        if tool.cost_estimate_max > 500:
            return "Start with minimum budget and scale if early results are positive"
        elif tool.time_estimate_days > 14:
            return "Set clear success/failure criteria upfront to avoid sunk cost"
        else:
            return "Low-risk approach - can pivot quickly if needed"

    def _calculate_confidence(self, steps: list[ValidationStep], payment_intent: float) -> str:
        """Calculate confidence level of validation plan."""
        if not steps:
            return "low"

        # More steps = higher confidence
        # Higher payment intent = higher confidence
        score = len(steps) + (payment_intent * 2)

        if score >= 4:
            return "high"
        elif score >= 2.5:
            return "medium"
        else:
            return "low"

    def _generate_strategy(
        self,
        steps: list[ValidationStep],
        budget: str,
        time_available: str,
        risk_tolerance: str
    ) -> str:
        """Generate overall validation strategy description."""
        if not steps:
            return "No validation steps recommended with current constraints"

        strategy_parts = []

        # Opening based on approach
        if risk_tolerance == "low":
            strategy_parts.append("Conservative validation approach:")
        elif risk_tolerance == "high":
            strategy_parts.append("Aggressive validation approach:")
        else:
            strategy_parts.append("Balanced validation approach:")

        # Describe the flow
        if len(steps) == 1:
            strategy_parts.append(f"Focus on {steps[0].tool.name.lower()} to quickly test the core hypothesis.")
        else:
            first_tools = ", ".join(s.tool.name for s in steps[:-1])
            last_tool = steps[-1].tool.name
            strategy_parts.append(
                f"Start with {first_tools}, then move to {last_tool} if initial results are positive."
            )

        # Add budget/time context
        if budget == "low":
            strategy_parts.append("All steps are designed to fit within a minimal budget.")
        if time_available == "short":
            strategy_parts.append("Focus on quick wins and fast feedback cycles.")

        return " ".join(strategy_parts)
