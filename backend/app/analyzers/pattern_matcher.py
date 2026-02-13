"""Pattern matcher for matching opportunities against success patterns.

Uses keyword matching and semantic similarity to find similar successful products.
"""

import re
from dataclasses import dataclass
from typing import Optional

from app.analyzers.success_patterns import SuccessPatternDatabase, SuccessPattern, Category


@dataclass
class PatternMatch:
    """A match between an opportunity and a success pattern."""
    pattern: SuccessPattern
    match_score: float  # 0.0-1.0
    matched_signals: list[str]
    category_match: bool
    pain_similarity: float  # 0.0-1.0


@dataclass
class PatternMatchResult:
    """Result of pattern matching."""
    matches: list[PatternMatch]
    best_match: Optional[PatternMatch]
    overall_score: float  # 0.0-10.0
    similar_successes: list[str]  # Company names


class PatternMatcher:
    """Matches opportunities against historical success patterns."""

    # Category keywords for auto-detection
    CATEGORY_KEYWORDS = {
        Category.COMMUNICATION: [
            "chat", "message", "email", "communication", "team", "slack", "discord",
            "voice", "call", "meeting", "video call", "collaborate",
        ],
        Category.PRODUCTIVITY: [
            "task", "project", "todo", "organize", "workflow", "manage", "schedule",
            "calendar", "notes", "wiki", "document", "spreadsheet", "board",
        ],
        Category.DEVELOPER_TOOLS: [
            "developer", "api", "code", "git", "deploy", "ci/cd", "testing",
            "debugging", "sdk", "library", "framework", "programming",
        ],
        Category.DESIGN: [
            "design", "ui", "ux", "prototype", "figma", "sketch", "graphics",
            "visual", "whiteboard", "diagram", "wireframe", "mockup",
        ],
        Category.MARKETING: [
            "marketing", "email campaign", "newsletter", "seo", "ads", "content",
            "social media", "analytics", "leads", "conversion",
        ],
        Category.SALES: [
            "sales", "crm", "leads", "pipeline", "deal", "revenue", "quota",
            "prospect", "outreach", "cold email",
        ],
        Category.HR: [
            "hr", "hiring", "recruit", "payroll", "employee", "onboarding",
            "benefits", "performance review", "remote work",
        ],
        Category.FINANCE: [
            "finance", "accounting", "invoice", "expense", "budget", "payment",
            "billing", "subscription", "revenue",
        ],
        Category.ANALYTICS: [
            "analytics", "metrics", "dashboard", "data", "tracking", "funnel",
            "retention", "cohort", "behavior",
        ],
        Category.SECURITY: [
            "security", "password", "authentication", "encryption", "privacy",
            "compliance", "audit", "access control",
        ],
        Category.NO_CODE: [
            "no-code", "low-code", "automation", "workflow", "integration",
            "zapier", "connect", "automate", "build without code",
        ],
        Category.ECOMMERCE: [
            "ecommerce", "store", "shop", "sell", "product", "inventory",
            "checkout", "cart", "merchant",
        ],
        Category.AI_ML: [
            "ai", "artificial intelligence", "machine learning", "ml", "gpt",
            "generate", "automate", "predict", "nlp",
        ],
        Category.VIDEO: [
            "video", "recording", "streaming", "screen capture", "loom",
            "tutorial", "demo", "async video",
        ],
    }

    # Pain point keywords for similarity matching
    PAIN_KEYWORDS = {
        "complexity": ["complex", "complicated", "hard", "difficult", "confusing"],
        "speed": ["slow", "time-consuming", "takes too long", "waiting", "hours"],
        "cost": ["expensive", "costly", "overpriced", "too much money", "budget"],
        "fragmentation": ["fragmented", "scattered", "multiple tools", "switching between"],
        "manual_work": ["manual", "tedious", "repetitive", "boring", "grunt work"],
        "collaboration": ["collaborate", "team", "together", "share", "real-time"],
        "reliability": ["unreliable", "buggy", "crashes", "down", "broken"],
        "scaling": ["scale", "grow", "enterprise", "team size", "volume"],
    }

    def __init__(self):
        """Initialize pattern matcher."""
        self.db = SuccessPatternDatabase()
        self._all_signals = self.db.get_all_signals()

    def match(self, text: str, category_hint: Optional[str] = None) -> PatternMatchResult:
        """Match text against success patterns.

        Args:
            text: The opportunity text to match
            category_hint: Optional category hint (e.g., "SaaS", "Productivity")

        Returns:
            PatternMatchResult with matches and scores
        """
        if not text:
            return PatternMatchResult(
                matches=[],
                best_match=None,
                overall_score=0.0,
                similar_successes=[]
            )

        text_lower = text.lower()

        # Extract signals from text
        found_signals = self._extract_signals(text_lower)

        # Detect likely categories
        detected_categories = self._detect_categories(text_lower, category_hint)

        # Analyze pain points
        pain_analysis = self._analyze_pain_points(text_lower)

        # Match against all patterns
        matches = []
        for pattern in self.db.get_all_patterns():
            match = self._match_pattern(
                pattern, text_lower, found_signals,
                detected_categories, pain_analysis
            )
            if match and match.match_score > 0.1:
                matches.append(match)

        # Sort by score
        matches.sort(key=lambda m: m.match_score, reverse=True)

        # Calculate overall score (0-10)
        if matches:
            # Top match contributes most, with bonus for multiple matches
            top_score = matches[0].match_score * 7
            match_count_bonus = min(3, len(matches) - 1) * 0.5
            overall_score = min(10, top_score + match_count_bonus)
        else:
            overall_score = 0.0

        return PatternMatchResult(
            matches=matches[:5],  # Top 5 matches
            best_match=matches[0] if matches else None,
            overall_score=round(overall_score, 1),
            similar_successes=[m.pattern.name for m in matches[:3]]
        )

    def _extract_signals(self, text: str) -> list[str]:
        """Extract signals from text that match known success pattern signals."""
        found = []
        for signal in self._all_signals:
            if signal.lower() in text:
                found.append(signal)
        return found

    def _detect_categories(
        self,
        text: str,
        category_hint: Optional[str]
    ) -> list[Category]:
        """Detect likely categories from text."""
        scores = {}

        for category, keywords in self.CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                scores[category] = score

        # Also consider category hint
        if category_hint:
            hint_lower = category_hint.lower()
            for category in Category:
                if category.value in hint_lower or hint_lower in category.value:
                    scores[category] = scores.get(category, 0) + 2

        # Return categories with highest scores
        if not scores:
            return []

        max_score = max(scores.values())
        return [cat for cat, score in scores.items() if score >= max_score * 0.5]

    def _analyze_pain_points(self, text: str) -> dict[str, float]:
        """Analyze pain point signals in text."""
        results = {}

        for pain_type, keywords in self.PAIN_KEYWORDS.items():
            matches = sum(1 for kw in keywords if kw in text)
            if matches > 0:
                results[pain_type] = min(1.0, matches / 2)

        return results

    def _match_pattern(
        self,
        pattern: SuccessPattern,
        text: str,
        found_signals: list[str],
        detected_categories: list[Category],
        pain_analysis: dict[str, float]
    ) -> Optional[PatternMatch]:
        """Match a single pattern against the text."""
        # Signal matching
        pattern_signals_lower = [s.lower() for s in pattern.signals]
        matched_signals = [s for s in found_signals if s.lower() in pattern_signals_lower]
        signal_score = len(matched_signals) / len(pattern.signals) if pattern.signals else 0

        # Category matching
        category_match = pattern.category in detected_categories

        # Pain similarity (check if pattern's pain words appear in text)
        pain_words = pattern.original_pain.lower().split()
        pain_matches = sum(1 for word in pain_words if len(word) > 3 and word in text)
        pain_similarity = min(1.0, pain_matches / max(3, len(pain_words) * 0.3))

        # Overall score calculation
        # Signal match is most important (50%)
        # Pain similarity (30%)
        # Category match (20%)
        match_score = (
            signal_score * 0.5 +
            pain_similarity * 0.3 +
            (0.2 if category_match else 0)
        )

        if match_score < 0.1:
            return None

        return PatternMatch(
            pattern=pattern,
            match_score=round(match_score, 3),
            matched_signals=matched_signals,
            category_match=category_match,
            pain_similarity=round(pain_similarity, 3)
        )

    def get_pattern_summary(self, pattern: SuccessPattern) -> str:
        """Get a human-readable summary of a pattern."""
        return (
            f"{pattern.name}: {pattern.original_pain} → "
            f"{pattern.solution_type} ({pattern.outcome_value})"
        )
