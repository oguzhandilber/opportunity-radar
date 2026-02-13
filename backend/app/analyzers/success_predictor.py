"""Success predictor for opportunity validation.

Combines pattern matching with other signals to predict success likelihood.
"""

from dataclasses import dataclass
from typing import Optional

from app.analyzers.pattern_matcher import PatternMatcher, PatternMatchResult
from app.analyzers.payment_signals import PaymentSignalDetector, PaymentSignalResult
from app.analyzers.competitor_extractor import CompetitorExtractor, CompetitorExtractionResult
from app.analyzers.journey_classifier import JourneyClassifier, JourneyClassificationResult, JourneyStage


@dataclass
class SuccessPrediction:
    """Success prediction result."""
    success_likelihood: float  # 0-100 percentage
    confidence: float  # 0-1
    factors: dict[str, float]  # Contributing factors and their scores
    recommendation: str  # Human-readable recommendation
    risk_level: str  # "low", "medium", "high"
    similar_successes: list[str]


class SuccessPredictor:
    """Predicts success likelihood for opportunities.

    Combines multiple signals:
    - Historical pattern matching (do similar ideas succeed?)
    - Payment intent (are people willing to pay?)
    - Market signals (competition, timing)
    - Journey stage (how ready are buyers?)
    """

    # Weight factors for prediction
    WEIGHTS = {
        "pattern_match": 0.30,  # Historical pattern match
        "payment_intent": 0.25,  # Payment signals
        "market_timing": 0.20,  # Existing competitors = validated market
        "journey_stage": 0.15,  # Buyer readiness
        "specificity": 0.10,   # How specific is the opportunity
    }

    def __init__(self):
        """Initialize predictor with all analyzers."""
        self.pattern_matcher = PatternMatcher()
        self.payment_detector = PaymentSignalDetector()
        self.competitor_extractor = CompetitorExtractor()
        self.journey_classifier = JourneyClassifier()

    def predict(
        self,
        text: str,
        category_hint: Optional[str] = None,
        pre_computed: Optional[dict] = None
    ) -> SuccessPrediction:
        """Predict success likelihood for an opportunity.

        Args:
            text: The opportunity text
            category_hint: Optional category hint
            pre_computed: Optional pre-computed analysis results

        Returns:
            SuccessPrediction with likelihood and factors
        """
        if not text:
            return SuccessPrediction(
                success_likelihood=0,
                confidence=0,
                factors={},
                recommendation="No content to analyze",
                risk_level="high",
                similar_successes=[]
            )

        # Get or compute analysis results
        if pre_computed:
            pattern_result = pre_computed.get("pattern_result")
            payment_result = pre_computed.get("payment_result")
            competitor_result = pre_computed.get("competitor_result")
            journey_result = pre_computed.get("journey_result")
        else:
            pattern_result = None
            payment_result = None
            competitor_result = None
            journey_result = None

        # Compute missing results
        if pattern_result is None:
            pattern_result = self.pattern_matcher.match(text, category_hint)
        if payment_result is None:
            payment_result = self.payment_detector.detect(text)
        if competitor_result is None:
            competitor_result = self.competitor_extractor.extract(text)
        if journey_result is None:
            journey_result = self.journey_classifier.classify(text)

        # Calculate individual factor scores (0-100)
        factors = {
            "pattern_match": self._score_pattern_match(pattern_result),
            "payment_intent": self._score_payment_intent(payment_result),
            "market_timing": self._score_market_timing(competitor_result),
            "journey_stage": self._score_journey_stage(journey_result),
            "specificity": self._score_specificity(text),
        }

        # Calculate weighted success likelihood
        success_likelihood = sum(
            factors[key] * self.WEIGHTS[key]
            for key in self.WEIGHTS
        )

        # Calculate confidence based on signal strength
        confidence = self._calculate_confidence(
            pattern_result, payment_result, competitor_result, journey_result
        )

        # Determine risk level
        risk_level = self._determine_risk_level(success_likelihood, factors)

        # Generate recommendation
        recommendation = self._generate_recommendation(
            success_likelihood, factors, pattern_result
        )

        return SuccessPrediction(
            success_likelihood=round(success_likelihood, 1),
            confidence=round(confidence, 2),
            factors={k: round(v, 1) for k, v in factors.items()},
            recommendation=recommendation,
            risk_level=risk_level,
            similar_successes=pattern_result.similar_successes if pattern_result else []
        )

    def _score_pattern_match(self, result: PatternMatchResult) -> float:
        """Score based on pattern matching (0-100)."""
        if not result or not result.matches:
            return 20  # Base score for new ideas

        # Best match score (0-10) * 8 + bonus for multiple matches
        base = result.overall_score * 8
        match_bonus = min(20, len(result.matches) * 5)
        return min(100, base + match_bonus)

    def _score_payment_intent(self, result: PaymentSignalResult) -> float:
        """Score based on payment intent (0-100)."""
        if not result or not result.has_signal:
            return 10  # Low base score without payment signals

        tier_scores = {
            1: 100,  # Already paying = validated
            2: 80,   # Ready to pay
            3: 70,   # Churning from competitor
            4: 40,   # Price aware
        }
        base = tier_scores.get(result.tier, 20)

        # Bonus for strength
        strength_bonus = result.strength * 20
        return min(100, base * 0.7 + strength_bonus)

    def _score_market_timing(self, result: CompetitorExtractionResult) -> float:
        """Score based on market timing/competition (0-100)."""
        if not result:
            return 30  # Unknown market

        # Some competition is good (validated market)
        # Too much competition is bad
        competitor_count = result.competitors_count

        if competitor_count == 0:
            return 40  # Unvalidated market
        elif competitor_count <= 2:
            return 80  # Sweet spot - validated but not crowded
        elif competitor_count <= 4:
            return 60  # Getting crowded
        else:
            return 40  # Very competitive

        # Bonus for churning (people leaving competitors)
        if result.has_churning:
            return min(100, 90)  # High score for active churning

    def _score_journey_stage(self, result: JourneyClassificationResult) -> float:
        """Score based on buyer journey stage (0-100)."""
        if not result:
            return 20

        stage_scores = {
            JourneyStage.CHURNING: 95,
            JourneyStage.READY: 90,
            JourneyStage.CONSIDERING: 60,
            JourneyStage.AWARE: 35,
            JourneyStage.UNAWARE: 15,
        }
        base = stage_scores.get(result.stage, 20)

        # Adjust by confidence
        return base * (0.5 + result.confidence * 0.5)

    def _score_specificity(self, text: str) -> float:
        """Score based on how specific the opportunity is (0-100)."""
        # More specific = better
        word_count = len(text.split())

        if word_count < 20:
            return 20  # Too vague
        elif word_count < 50:
            return 50
        elif word_count < 150:
            return 80
        else:
            return 70  # Very long might be unfocused

    def _calculate_confidence(
        self,
        pattern_result: PatternMatchResult,
        payment_result: PaymentSignalResult,
        competitor_result: CompetitorExtractionResult,
        journey_result: JourneyClassificationResult
    ) -> float:
        """Calculate prediction confidence based on signal strength."""
        signals = 0
        total_signals = 4

        if pattern_result and pattern_result.matches:
            signals += 1
        if payment_result and payment_result.has_signal:
            signals += 1
        if competitor_result and competitor_result.mentions:
            signals += 1
        if journey_result and journey_result.stage != JourneyStage.UNAWARE:
            signals += 1

        # Base confidence from signal count
        base_confidence = signals / total_signals

        # Boost for strong individual signals
        boost = 0
        if pattern_result and pattern_result.overall_score >= 7:
            boost += 0.1
        if payment_result and payment_result.tier in [1, 2]:
            boost += 0.1
        if journey_result and journey_result.stage in [JourneyStage.READY, JourneyStage.CHURNING]:
            boost += 0.1

        return min(1.0, base_confidence + boost)

    def _determine_risk_level(
        self,
        success_likelihood: float,
        factors: dict[str, float]
    ) -> str:
        """Determine risk level."""
        if success_likelihood >= 70:
            return "low"
        elif success_likelihood >= 45:
            return "medium"
        else:
            return "high"

    def _generate_recommendation(
        self,
        success_likelihood: float,
        factors: dict[str, float],
        pattern_result: PatternMatchResult
    ) -> str:
        """Generate human-readable recommendation."""
        if success_likelihood >= 75:
            rec = "Strong opportunity! "
            if pattern_result and pattern_result.best_match:
                rec += f"Similar to {pattern_result.best_match.pattern.name}'s success. "
            rec += "Consider validating with a landing page."
            return rec

        elif success_likelihood >= 55:
            rec = "Promising opportunity. "
            weak_factors = [k for k, v in factors.items() if v < 50]
            if weak_factors:
                rec += f"Strengthen: {', '.join(weak_factors)}. "
            rec += "Needs more validation."
            return rec

        elif success_likelihood >= 35:
            rec = "Moderate potential. "
            if factors.get("payment_intent", 0) < 40:
                rec += "Payment intent signals are weak. "
            if factors.get("pattern_match", 0) < 40:
                rec += "No clear success pattern match. "
            rec += "Validate thoroughly before investing."
            return rec

        else:
            rec = "Low success indicators. "
            if not pattern_result or not pattern_result.matches:
                rec += "No similar successful products found. "
            if factors.get("journey_stage", 0) < 30:
                rec += "Buyers not ready. "
            rec += "Consider pivoting or gathering more evidence."
            return rec
