"""Price extraction from text content.

Extracts mentioned prices, budgets, and cost references.
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class ExtractedPrice:
    """A single extracted price."""
    amount: float
    currency: str
    period: Optional[str]  # month, year, one-time, None
    context: str  # The surrounding text
    price_type: str  # budget, current_spend, willing_to_pay, mentioned, etc.


@dataclass
class PriceExtractionResult:
    """Result of price extraction."""
    prices: list[ExtractedPrice]
    min_price: Optional[float]
    max_price: Optional[float]
    avg_price: Optional[float]
    has_recurring: bool
    monthly_equivalent: Optional[float]  # Normalized to monthly


class PriceExtractor:
    """Extracts price information from text."""

    # Price patterns with context
    PRICE_PATTERNS = [
        # Direct amounts: $50, $50/month, $50 per month
        (
            r"(?P<currency>\$|USD|EUR|€|£)?\s*(?P<amount>\d{1,6}(?:,\d{3})*(?:\.\d{2})?)\s*"
            r"(?:(?P<period_sep>/|per\s*|a\s*)(?P<period>month|mo|year|yr|annual|week|wk|day|user|seat))?",
            "amount_first"
        ),
        # Amounts with k notation: $5k, $50k/year
        (
            r"(?P<currency>\$|USD|EUR|€|£)\s*(?P<amount>\d{1,3})(?P<multiplier>k|K)\s*"
            r"(?:(?P<period_sep>/|per\s*)(?P<period>month|mo|year|yr|annual))?",
            "k_notation"
        ),
    ]

    # Context patterns to determine price type
    CONTEXT_PATTERNS = {
        "budget": [
            r"budget (?:is|of|around)",
            r"have \$",
            r"can spend",
            r"willing to spend",
        ],
        "current_spend": [
            r"paying",
            r"spend(?:ing)?",
            r"costs? (?:us|me)",
            r"subscribed.*for",
        ],
        "willing_to_pay": [
            r"would pay",
            r"i'?d pay",
            r"willing to pay",
            r"ready to pay",
            r"pay up to",
        ],
        "too_expensive": [
            r"too (?:much|expensive)",
            r"costs? too",
            r"can'?t afford",
            r"overpriced",
        ],
        "comparison": [
            r"cheaper than",
            r"more than",
            r"less than",
            r"compared to",
            r"vs\.?",
        ],
    }

    # Period normalization to months
    PERIOD_TO_MONTHS = {
        "month": 1,
        "mo": 1,
        "year": 12,
        "yr": 12,
        "annual": 12,
        "week": 0.25,
        "wk": 0.25,
        "day": 1/30,
    }

    def __init__(self):
        """Initialize with compiled patterns."""
        self._compiled_price_patterns = [
            (re.compile(p, re.IGNORECASE), name)
            for p, name in self.PRICE_PATTERNS
        ]
        self._compiled_context_patterns = {
            ptype: [re.compile(p, re.IGNORECASE) for p in patterns]
            for ptype, patterns in self.CONTEXT_PATTERNS.items()
        }

    def extract(self, text: str) -> PriceExtractionResult:
        """Extract all prices from text.

        Args:
            text: Text to analyze

        Returns:
            PriceExtractionResult with all found prices
        """
        if not text:
            return PriceExtractionResult(
                prices=[],
                min_price=None,
                max_price=None,
                avg_price=None,
                has_recurring=False,
                monthly_equivalent=None
            )

        prices = []

        for pattern, pattern_type in self._compiled_price_patterns:
            for match in pattern.finditer(text):
                price = self._parse_match(match, pattern_type, text)
                if price and price.amount > 0:
                    prices.append(price)

        if not prices:
            return PriceExtractionResult(
                prices=[],
                min_price=None,
                max_price=None,
                avg_price=None,
                has_recurring=False,
                monthly_equivalent=None
            )

        # Calculate statistics
        amounts = [p.amount for p in prices]
        has_recurring = any(p.period is not None for p in prices)

        # Calculate monthly equivalent from the most relevant recurring price
        monthly_equivalent = None
        for price in prices:
            if price.period:
                months = self.PERIOD_TO_MONTHS.get(price.period, 1)
                monthly_equivalent = price.amount / months if months > 0 else price.amount
                break

        return PriceExtractionResult(
            prices=prices,
            min_price=min(amounts),
            max_price=max(amounts),
            avg_price=round(sum(amounts) / len(amounts), 2),
            has_recurring=has_recurring,
            monthly_equivalent=round(monthly_equivalent, 2) if monthly_equivalent else None
        )

    def _parse_match(
        self,
        match: re.Match,
        pattern_type: str,
        full_text: str
    ) -> Optional[ExtractedPrice]:
        """Parse a regex match into an ExtractedPrice."""
        try:
            groups = match.groupdict()

            # Parse amount
            amount_str = groups.get("amount", "0")
            amount_str = amount_str.replace(",", "")
            amount = float(amount_str)

            # Handle k notation
            if pattern_type == "k_notation" and groups.get("multiplier"):
                amount *= 1000

            # Skip unrealistic amounts
            if amount < 1 or amount > 1_000_000:
                return None

            # Parse currency
            currency = groups.get("currency", "$") or "$"
            currency_map = {"USD": "$", "EUR": "€", "£": "£"}
            currency = currency_map.get(currency, currency)

            # Parse period
            period = groups.get("period")
            if period:
                period = period.lower()
                # Normalize period names
                period_map = {"mo": "month", "yr": "year", "wk": "week", "annual": "year"}
                period = period_map.get(period, period)

            # Get context (50 chars before and after)
            start = max(0, match.start() - 50)
            end = min(len(full_text), match.end() + 50)
            context = full_text[start:end].strip()

            # Determine price type from context
            price_type = self._determine_price_type(context)

            return ExtractedPrice(
                amount=amount,
                currency=currency,
                period=period,
                context=context,
                price_type=price_type
            )

        except (ValueError, KeyError):
            return None

    def _determine_price_type(self, context: str) -> str:
        """Determine the type of price from surrounding context."""
        for price_type, patterns in self._compiled_context_patterns.items():
            for pattern in patterns:
                if pattern.search(context):
                    return price_type
        return "mentioned"
