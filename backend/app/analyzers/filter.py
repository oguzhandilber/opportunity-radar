"""Content filter for spam and noise elimination."""

import re


class ContentFilter:
    """Filter out spam, noise, and irrelevant content."""

    # Minimum content length
    MIN_LENGTH = 50

    # Maximum content length (to avoid extremely long posts)
    MAX_LENGTH = 10000

    # Spam indicators
    SPAM_PATTERNS = [
        r"\b(buy now|limited time|act fast|click here)\b",
        r"\b(crypto|nft|bitcoin|ethereum)\s+(giveaway|airdrop)\b",
        r"\b(earn \$\d+|make money fast)\b",
        r"\b(dm me|check bio|link in bio)\b",
        r"(🚀){3,}",  # Multiple rocket emojis often indicate spam
        r"\b(upvote|please upvote|need karma)\b",
    ]

    # Irrelevant content patterns
    IRRELEVANT_PATTERNS = [
        r"^(test|testing|hello world)$",
        r"\b(meme|joke|funny|lol|lmao)\b",
        r"\b(unpopular opinion|change my mind|cmv)\b",
    ]

    # HIGH PRIORITY: Payment intent signals (Pivot 3)
    # These indicate real buying intent - prioritize these
    PAYMENT_INTENT_SIGNALS = [
        r"\b(i'm paying|paying \$|spend(?:ing)? \$)\b",
        r"\b(would pay|i'd pay|willing to pay|ready to pay)\b",
        r"\b(budget (?:is|of)|can spend)\b",
        r"\b(cancel(?:l)?ing|switching from|leaving .{1,20} because)\b",
        r"\b(looking for .{1,30} alternative)\b",
        r"\b(take my money|shut up and take)\b",
        r"\b(where can i (?:buy|purchase))\b",
    ]

    # Standard opportunity signals (lower priority than payment signals)
    OPPORTUNITY_SIGNALS = [
        r"\b(need|want|wish|looking for)\b.*\b(tool|app|solution|service|software)\b",
        r"\b(frustrated|annoyed|tired of)\b",
        r"\b(there should be|someone should make|why isn't there)\b",
        r"\b(would pay|i'd pay|pay for)\b",
        r"\b(alternative to|replacement for)\b",
        r"\b(problem|issue|challenge|pain point)\b",
        r"\b(idea|concept|proposal|suggestion)\b",
        r"\b(startup|saas|business|product)\b",
        r"\b(market|opportunity|trend|growing)\b",
    ]

    def __init__(self):
        self.spam_regex = [re.compile(p, re.IGNORECASE) for p in self.SPAM_PATTERNS]
        self.irrelevant_regex = [re.compile(p, re.IGNORECASE) for p in self.IRRELEVANT_PATTERNS]
        self.payment_regex = [re.compile(p, re.IGNORECASE) for p in self.PAYMENT_INTENT_SIGNALS]
        self.opportunity_regex = [re.compile(p, re.IGNORECASE) for p in self.OPPORTUNITY_SIGNALS]

    def is_relevant(self, content: str) -> bool:
        """Check if content is relevant for opportunity analysis."""
        # Length check
        if len(content) < self.MIN_LENGTH:
            return False
        if len(content) > self.MAX_LENGTH:
            content = content[: self.MAX_LENGTH]

        # Spam check
        for pattern in self.spam_regex:
            if pattern.search(content):
                return False

        # Irrelevant check
        for pattern in self.irrelevant_regex:
            if pattern.search(content):
                return False

        # Payment signals are always relevant (high priority)
        if any(pattern.search(content) for pattern in self.payment_regex):
            return True

        # Standard opportunity signal check (at least one should match)
        has_signal = any(pattern.search(content) for pattern in self.opportunity_regex)

        return has_signal

    def has_payment_intent(self, content: str) -> bool:
        """Check if content has payment intent signals (Pivot 3)."""
        return any(pattern.search(content) for pattern in self.payment_regex)

    def clean_content(self, content: str) -> str:
        """Clean content for analysis."""
        # Remove URLs
        content = re.sub(r"http\S+|www\.\S+", "[URL]", content)

        # Remove excessive whitespace
        content = re.sub(r"\s+", " ", content)

        # Truncate if too long
        if len(content) > self.MAX_LENGTH:
            content = content[: self.MAX_LENGTH] + "..."

        return content.strip()
