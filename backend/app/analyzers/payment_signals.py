"""Payment signal detection for opportunity analysis.

Detects signals indicating payment intent or willingness to pay.
Uses a 4-tier system based on signal strength.
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class PaymentSignalResult:
    """Result of payment signal detection."""
    has_signal: bool
    tier: Optional[int]  # 1-4, None if no signal
    strength: float  # 0.0-1.0
    matches: list[dict]  # List of {pattern, match, tier}


class PaymentSignalDetector:
    """Detects payment intent signals in text.

    Tier System:
    - Tier 1: Already paying (strongest) - They have budget, spending now
    - Tier 2: Active buyer - Actively looking to purchase
    - Tier 3: Churning - Leaving a competitor, ready to switch
    - Tier 4: Price awareness - Discussing prices, may convert
    """

    # Tier 1: Already paying - strongest signal
    # These people have budget and are actively spending
    TIER_1_PATTERNS = [
        (r"\bi['\u2019]?m paying \$?(\d+)", "currently_paying"),
        (r"\bpay(?:ing)? \$(\d+)(?:/|\s*per\s*)(month|mo|year|yr)", "recurring_payment"),
        (r"\bspend(?:ing)? \$(\d+)(?:/|\s*per\s*)(month|mo|year|yr)", "recurring_spend"),
        (r"\bour budget is \$?(\d+)", "stated_budget"),
        (r"\bwe spend \$?(\d+)", "team_spending"),
        (r"\bcurrently using .{1,30} at \$(\d+)", "current_tool_cost"),
        (r"\bsubscribed to .{1,30} for \$(\d+)", "active_subscription"),
    ]

    # Tier 2: Active buyer - ready to purchase
    TIER_2_PATTERNS = [
        (r"\bwilling to pay", "willing_to_pay"),
        (r"\bwould pay \$?(\d+)", "would_pay_amount"),
        (r"\bi['\u2019]?d pay \$?(\d+)", "would_pay_amount"),
        (r"\bbudget of \$?(\d+)", "has_budget"),
        (r"\blooking to buy", "looking_to_buy"),
        (r"\bready to (pay|purchase|buy)", "ready_to_pay"),
        (r"\bneed to (purchase|buy)", "need_to_buy"),
        (r"\bwant to (purchase|buy)", "want_to_buy"),
        (r"\btake my money", "take_my_money"),
        (r"\bshut up and take my money", "shut_up_take_money"),
        (r"\bwhere can i (buy|purchase|pay)", "asking_to_buy"),
        (r"\bhow (?:much|do i pay)", "asking_price"),
    ]

    # Tier 3: Churning - leaving competitor, high intent
    TIER_3_PATTERNS = [
        (r"\b(cancell?ing|cancel(?:l)?ed) (?:my |our )?.{1,30}subscription", "canceling_sub"),
        (r"\bswitching from", "switching_from"),
        (r"\bleaving .{1,30} because", "leaving_because"),
        (r"\bquit(?:ting)? .{1,30} because", "quitting_because"),
        (r"\btired of (paying|spending)", "tired_of_paying"),
        (r"\b(ditching|dropping|abandoning) .{1,20}", "abandoning_tool"),
        (r"\blooking for .{1,30} alternative", "seeking_alternative"),
        (r"\b.{1,20} (sucks|is terrible|is garbage)", "tool_frustration"),
        (r"\bfed up with .{1,20}", "fed_up"),
        (r"\bmoving away from", "moving_away"),
    ]

    # Tier 4: Price awareness - discussing prices
    TIER_4_PATTERNS = [
        (r"\bcosts? too much", "too_expensive"),
        (r"\btoo expensive", "too_expensive"),
        (r"\bcheaper than", "price_comparison"),
        (r"\bmore affordable", "seeking_affordable"),
        (r"\bworth \$?(\d+)", "worth_amount"),
        (r"\bprice(?:d)? at \$?(\d+)", "priced_at"),
        (r"\b\$(\d+)(?:/|\s*per\s*)(month|mo|year|yr|user)", "price_mention"),
        (r"\bfree (?:trial|tier|plan)", "free_tier_interest"),
        (r"\bpricing", "discussing_pricing"),
        (r"\bROI", "discussing_roi"),
        (r"\bcost.{1,10}benefit", "cost_benefit"),
    ]

    # Tier weights for strength calculation
    TIER_WEIGHTS = {
        1: 1.0,
        2: 0.8,
        3: 0.7,
        4: 0.4,
    }

    def __init__(self):
        """Initialize detector with compiled patterns."""
        self._compiled_patterns = {
            1: [(re.compile(p, re.IGNORECASE), name) for p, name in self.TIER_1_PATTERNS],
            2: [(re.compile(p, re.IGNORECASE), name) for p, name in self.TIER_2_PATTERNS],
            3: [(re.compile(p, re.IGNORECASE), name) for p, name in self.TIER_3_PATTERNS],
            4: [(re.compile(p, re.IGNORECASE), name) for p, name in self.TIER_4_PATTERNS],
        }

    def detect(self, text: str) -> PaymentSignalResult:
        """Detect payment signals in text.

        Args:
            text: Text to analyze

        Returns:
            PaymentSignalResult with detection results
        """
        if not text:
            return PaymentSignalResult(
                has_signal=False,
                tier=None,
                strength=0.0,
                matches=[]
            )

        matches = []
        best_tier = None

        # Check each tier in order (1 is best)
        for tier in [1, 2, 3, 4]:
            for pattern, name in self._compiled_patterns[tier]:
                for match in pattern.finditer(text):
                    matches.append({
                        "pattern": name,
                        "match": match.group(0),
                        "tier": tier,
                        "start": match.start(),
                        "end": match.end(),
                    })
                    if best_tier is None or tier < best_tier:
                        best_tier = tier

        if not matches:
            return PaymentSignalResult(
                has_signal=False,
                tier=None,
                strength=0.0,
                matches=[]
            )

        # Calculate strength based on best tier and number of matches
        base_strength = self.TIER_WEIGHTS.get(best_tier, 0.3)
        # Bonus for multiple matches (up to 20% bonus)
        match_bonus = min(0.2, len(matches) * 0.05)
        strength = min(1.0, base_strength + match_bonus)

        return PaymentSignalResult(
            has_signal=True,
            tier=best_tier,
            strength=round(strength, 2),
            matches=matches
        )

    def get_tier_description(self, tier: int) -> str:
        """Get human-readable description of tier."""
        descriptions = {
            1: "Already Paying - Active spender with confirmed budget",
            2: "Active Buyer - Ready and willing to purchase",
            3: "Churning - Leaving competitor, high conversion potential",
            4: "Price Aware - Discussing costs, potential buyer",
        }
        return descriptions.get(tier, "Unknown tier")
