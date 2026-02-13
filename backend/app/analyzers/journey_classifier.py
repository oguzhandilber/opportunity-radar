"""Purchase journey classification.

Classifies where a potential customer is in their buying journey.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class JourneyStage(Enum):
    """Stages in the purchase journey."""
    UNAWARE = "unaware"  # Doesn't know they have a problem
    AWARE = "aware"  # Knows the problem, exploring
    CONSIDERING = "considering"  # Actively evaluating solutions
    READY = "ready"  # Ready to purchase
    CHURNING = "churning"  # Leaving current solution


@dataclass
class JourneyClassificationResult:
    """Result of journey classification."""
    stage: JourneyStage
    confidence: float  # 0.0-1.0
    signals: list[str]  # What signals led to this classification
    conversion_potential: str  # "high", "medium", "low"


class JourneyClassifier:
    """Classifies purchase journey stage.

    Uses signals from text to determine where someone is in their
    buying journey, from unaware to ready to purchase.
    """

    # Stage patterns - checked in order from most valuable (CHURNING/READY) to least
    STAGE_PATTERNS = {
        JourneyStage.CHURNING: [
            (r"(?:leaving|left|quitting|quit|ditching|abandoning)", "leaving_current", 0.9),
            (r"(?:cancell?ing|cancell?ed)\s+(?:my|our)?\s*(?:subscription|account)", "canceling", 0.9),
            (r"switching\s+(?:from|away)", "switching_from", 0.85),
            (r"(?:fed up|tired|sick)\s+(?:of|with)", "frustration", 0.8),
            (r"looking for\s+(?:an?\s+)?alternative", "seeking_alternative", 0.85),
            (r"(?:replace|replacing|replaced)", "replacing", 0.8),
        ],
        JourneyStage.READY: [
            (r"(?:ready to|want to|need to)\s+(?:buy|purchase|pay)", "ready_to_buy", 0.95),
            (r"(?:take my money|shut up and take)", "take_my_money", 0.95),
            (r"where (?:can|do) i (?:buy|purchase|sign up)", "asking_to_buy", 0.9),
            (r"(?:willing|happy) to pay", "willing_to_pay", 0.9),
            (r"(?:budget|spend)\s+(?:is|of)\s+\$", "has_budget", 0.85),
            (r"(?:how much|what(?:'s| is) the price)", "asking_price", 0.85),
            (r"(?:pricing|plans|tiers)", "checking_pricing", 0.7),
            (r"(?:free trial|demo|try)", "trial_interest", 0.75),
        ],
        JourneyStage.CONSIDERING: [
            (r"(?:comparing|comparison|compare|vs\.?|versus)", "comparing", 0.8),
            (r"(?:which|what)\s+(?:is the best|should i)", "asking_recommendation", 0.75),
            (r"(?:pros and cons|advantages|disadvantages)", "evaluating", 0.75),
            (r"(?:reviews?|testimonials?|experiences?)", "seeking_reviews", 0.7),
            (r"anyone (?:use|using|tried|recommend)", "seeking_validation", 0.75),
            (r"(?:better than|worse than|instead of)", "comparing_options", 0.7),
            (r"(?:looking for|searching for|need)\s+(?:a|an)\s+(?:tool|app|solution|service)", "looking_for_solution", 0.7),
        ],
        JourneyStage.AWARE: [
            (r"(?:i wish|if only|would be nice)", "wishful", 0.6),
            (r"(?:frustrated|annoyed|tired of)\s+(?:with|by|of)?", "frustration_general", 0.6),
            (r"(?:there should be|why isn't there)", "identifying_gap", 0.65),
            (r"(?:i hate|i can't stand)", "pain_expression", 0.6),
            (r"(?:is there|does anyone know)", "exploratory", 0.55),
            (r"(?:problem|issue|challenge|struggle)", "problem_aware", 0.5),
        ],
    }

    # Conversion potential by stage
    CONVERSION_POTENTIAL = {
        JourneyStage.CHURNING: "high",
        JourneyStage.READY: "high",
        JourneyStage.CONSIDERING: "medium",
        JourneyStage.AWARE: "low",
        JourneyStage.UNAWARE: "very_low",
    }

    def __init__(self):
        """Initialize with compiled patterns."""
        self._compiled_patterns = {}
        for stage, patterns in self.STAGE_PATTERNS.items():
            self._compiled_patterns[stage] = [
                (re.compile(p, re.IGNORECASE), name, weight)
                for p, name, weight in patterns
            ]

    def classify(self, text: str) -> JourneyClassificationResult:
        """Classify the purchase journey stage.

        Args:
            text: Text to analyze

        Returns:
            JourneyClassificationResult with stage and signals
        """
        if not text:
            return JourneyClassificationResult(
                stage=JourneyStage.UNAWARE,
                confidence=0.0,
                signals=[],
                conversion_potential="very_low"
            )

        # Check stages in order of value (churning first, then ready, etc.)
        stage_order = [
            JourneyStage.CHURNING,
            JourneyStage.READY,
            JourneyStage.CONSIDERING,
            JourneyStage.AWARE,
        ]

        best_stage = JourneyStage.UNAWARE
        best_confidence = 0.0
        all_signals = []

        for stage in stage_order:
            stage_signals = []
            stage_weights = []

            for pattern, signal_name, weight in self._compiled_patterns[stage]:
                if pattern.search(text):
                    stage_signals.append(signal_name)
                    stage_weights.append(weight)
                    all_signals.append(f"{stage.value}:{signal_name}")

            if stage_signals:
                # Calculate confidence as max weight + bonus for multiple signals
                max_weight = max(stage_weights)
                bonus = min(0.1, len(stage_signals) * 0.02)
                confidence = min(1.0, max_weight + bonus)

                # First matching stage (in priority order) wins
                if best_stage == JourneyStage.UNAWARE:
                    best_stage = stage
                    best_confidence = confidence

        return JourneyClassificationResult(
            stage=best_stage,
            confidence=round(best_confidence, 2),
            signals=all_signals,
            conversion_potential=self.CONVERSION_POTENTIAL[best_stage]
        )

    def get_stage_description(self, stage: JourneyStage) -> str:
        """Get human-readable stage description."""
        descriptions = {
            JourneyStage.UNAWARE: "Unaware - No clear buying signals",
            JourneyStage.AWARE: "Aware - Knows they have a problem",
            JourneyStage.CONSIDERING: "Considering - Actively evaluating options",
            JourneyStage.READY: "Ready - Ready to make a purchase",
            JourneyStage.CHURNING: "Churning - Leaving current solution",
        }
        return descriptions.get(stage, "Unknown")

    def get_recommended_action(self, stage: JourneyStage) -> str:
        """Get recommended outreach action for stage."""
        actions = {
            JourneyStage.UNAWARE: "Not recommended - no buying intent",
            JourneyStage.AWARE: "Educational content, problem validation",
            JourneyStage.CONSIDERING: "Comparison content, social proof, demos",
            JourneyStage.READY: "Direct outreach, pricing discussion, trial offer",
            JourneyStage.CHURNING: "Immediate outreach, migration assistance, switching incentives",
        }
        return actions.get(stage, "Unknown")
