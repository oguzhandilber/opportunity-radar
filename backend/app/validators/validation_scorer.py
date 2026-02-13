"""Validation scorer for opportunities."""

from typing import TypedDict


class ValidationScore(TypedDict):
    """Validation score result."""

    total_score: float
    specificity: float
    actionability: float
    testability: float
    recommended_experiments: list[dict[str, str]]


class ValidationScorer:
    """Score opportunities based on validation potential."""

    @staticmethod
    def score_opportunity(
        title: str,
        summary: str | None,
        product_type: str | None,
        sector: str | None,
        suggested_features: list | None,
        competitors: list | None,
    ) -> ValidationScore:
        """Score an opportunity's validation potential.

        Args:
            title: Opportunity title
            summary: Opportunity summary
            product_type: Product type
            sector: Industry sector
            suggested_features: List of suggested features
            competitors: List of competitors

        Returns:
            ValidationScore with scoring breakdown and recommended experiments
        """
        specificity = ValidationScorer._score_specificity(
            title, summary, product_type, sector
        )
        actionability = ValidationScorer._score_actionability(
            suggested_features, competitors
        )
        testability = ValidationScorer._score_testability(
            product_type, summary, suggested_features
        )

        total_score = (specificity + actionability + testability) / 3

        recommended_experiments = ValidationScorer._recommend_experiments(
            total_score, specificity, actionability, testability, product_type
        )

        return ValidationScore(
            total_score=round(total_score, 2),
            specificity=round(specificity, 2),
            actionability=round(actionability, 2),
            testability=round(testability, 2),
            recommended_experiments=recommended_experiments,
        )

    @staticmethod
    def _score_specificity(
        title: str,
        summary: str | None,
        product_type: str | None,
        sector: str | None,
    ) -> float:
        """Score how specific and clear the opportunity is.

        Returns:
            Score from 0-10
        """
        score = 0.0

        # Title clarity (0-3 points)
        if title:
            # Longer, more descriptive titles are better
            if len(title) > 20:
                score += 1.5
            if len(title) > 40:
                score += 1.5
            # Check for specific keywords
            specific_keywords = [
                "for",
                "tool",
                "platform",
                "app",
                "software",
                "service",
                "solution",
            ]
            if any(keyword in title.lower() for keyword in specific_keywords):
                score += 1.0

        # Summary detail (0-4 points)
        if summary:
            if len(summary) > 100:
                score += 2.0
            if len(summary) > 200:
                score += 2.0

        # Classification (0-3 points)
        if product_type:
            score += 1.5
        if sector:
            score += 1.5

        return min(score, 10.0)

    @staticmethod
    def _score_actionability(
        suggested_features: list | None,
        competitors: list | None,
    ) -> float:
        """Score how actionable and implementable the opportunity is.

        Returns:
            Score from 0-10
        """
        score = 0.0

        # Features defined (0-6 points)
        if suggested_features:
            num_features = len(suggested_features)
            if num_features >= 1:
                score += 2.0
            if num_features >= 3:
                score += 2.0
            if num_features >= 5:
                score += 2.0

        # Competitor landscape (0-4 points)
        if competitors:
            num_competitors = len(competitors)
            if num_competitors >= 1:
                score += 2.0
            if num_competitors >= 3:
                score += 2.0

        return min(score, 10.0)

    @staticmethod
    def _score_testability(
        product_type: str | None,
        summary: str | None,
        suggested_features: list | None,
    ) -> float:
        """Score how testable the opportunity is with validation experiments.

        Returns:
            Score from 0-10
        """
        score = 5.0  # Base score

        # Some product types are easier to test
        easy_to_test = ["SaaS", "Web App", "Chrome Extension", "Mobile App"]
        if product_type and product_type in easy_to_test:
            score += 2.0

        # Problem-solution fit is easier to test
        if summary:
            problem_keywords = [
                "problem",
                "issue",
                "struggle",
                "difficult",
                "frustrating",
                "pain",
                "need",
            ]
            if any(keyword in summary.lower() for keyword in problem_keywords):
                score += 1.5

        # Multiple features = more to test
        if suggested_features and len(suggested_features) >= 3:
            score += 1.5

        return min(score, 10.0)

    @staticmethod
    def _recommend_experiments(
        total_score: float,
        specificity: float,
        actionability: float,
        testability: float,
        product_type: str | None,
    ) -> list[dict[str, str]]:
        """Recommend validation experiments based on scores.

        Args:
            total_score: Overall validation score
            specificity: Specificity score
            actionability: Actionability score
            testability: Testability score
            product_type: Product type

        Returns:
            List of recommended experiments with type and reason
        """
        experiments = []

        # Always recommend waitlist for high validation potential
        if total_score >= 7.0:
            experiments.append(
                {
                    "type": "waitlist",
                    "reason": "High validation potential - test demand with waitlist",
                    "priority": "high",
                }
            )

        # Recommend problem-solution landing page if specific
        if specificity >= 6.0 and actionability >= 5.0:
            experiments.append(
                {
                    "type": "problem_solution",
                    "reason": "Clear problem and solution - validate with landing page",
                    "priority": "high",
                }
            )

        # Recommend feature voting if many features
        if actionability >= 7.0:
            experiments.append(
                {
                    "type": "feature_vote",
                    "reason": "Multiple features identified - prioritize with user voting",
                    "priority": "medium",
                }
            )

        # Default: Start with waitlist
        if not experiments:
            experiments.append(
                {
                    "type": "waitlist",
                    "reason": "Start validation with simple waitlist",
                    "priority": "medium",
                }
            )

        # Add product-specific recommendations
        if product_type in ["SaaS", "Web App"]:
            experiments.append(
                {
                    "type": "problem_solution",
                    "reason": f"{product_type} is well-suited for landing page testing",
                    "priority": "medium",
                }
            )

        return experiments
