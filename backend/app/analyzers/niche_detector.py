"""Niche detector for multi-label classification of opportunities.

Detects which niche(s) an opportunity belongs to with confidence scores.
Supports multi-label classification where an opportunity can belong to multiple niches.
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional

from app.analyzers.niche_database import get_all_niches, get_niche


@dataclass
class NicheMatch:
    """A niche match with confidence score."""

    niche_id: str
    niche_name: str
    confidence: float  # 0.0-1.0
    matched_keywords: List[str]
    matched_pain_points: List[str]


@dataclass
class NicheDetectionResult:
    """Result of niche detection."""

    matches: List[NicheMatch]  # All matches sorted by confidence
    primary_niche: Optional[NicheMatch]  # Highest confidence match
    is_multi_niche: bool  # True if matches multiple niches
    total_keywords_matched: int


class NicheDetector:
    """Detects which niche(s) an opportunity belongs to.

    Uses keyword matching and pain point detection to classify opportunities
    into one or more niches. Returns confidence scores for each match.
    """

    # Minimum confidence threshold for a niche match
    MIN_CONFIDENCE = 0.15

    # Confidence threshold for secondary niches
    SECONDARY_THRESHOLD = 0.25

    def __init__(self):
        """Initialize detector with niche definitions."""
        self.niches = get_all_niches()
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for efficient matching."""
        self._niche_patterns = {}

        for niche in self.niches:
            # Compile keyword patterns
            keyword_patterns = []
            for keyword in niche.keywords:
                # Create word boundary pattern for whole word matching
                # Handle multi-word keywords
                if " " in keyword:
                    # Multi-word: match as phrase
                    pattern = re.escape(keyword)
                else:
                    # Single word: use word boundaries
                    pattern = r"\b" + re.escape(keyword) + r"\b"
                keyword_patterns.append(re.compile(pattern, re.IGNORECASE))

            # Compile pain point patterns
            pain_point_patterns = []
            for pain in niche.pain_points:
                # Extract key phrases from pain points (simplified)
                # Just match key words from the pain point
                words = pain.lower().split()
                # Take significant words (3+ chars)
                key_words = [w for w in words if len(w) >= 3 and w not in {
                    "and", "the", "for", "with", "from", "that", "this", "have",
                    "are", "was", "were", "been", "being", "has", "had"
                }]
                if key_words:
                    # Match if we find the key phrase
                    phrase = " ".join(key_words[:3])  # Use first 3 significant words
                    pain_point_patterns.append((re.compile(re.escape(phrase), re.IGNORECASE), pain))

            self._niche_patterns[niche.id] = {
                "keywords": keyword_patterns,
                "pain_points": pain_point_patterns,
                "keyword_strings": niche.keywords,  # For reporting
            }

    def detect(self, text: str, sector_hint: Optional[str] = None) -> NicheDetectionResult:
        """Detect niche(s) for the given text.

        Args:
            text: Text to analyze (post content, title, summary, etc.)
            sector_hint: Optional sector hint from previous classification

        Returns:
            NicheDetectionResult with all matches and primary niche
        """
        if not text:
            return NicheDetectionResult(
                matches=[],
                primary_niche=None,
                is_multi_niche=False,
                total_keywords_matched=0
            )

        matches = []
        total_keywords = 0

        for niche in self.niches:
            patterns = self._niche_patterns[niche.id]

            # Count keyword matches
            matched_keywords = []
            for i, pattern in enumerate(patterns["keywords"]):
                if pattern.search(text):
                    matched_keywords.append(patterns["keyword_strings"][i])

            # Count pain point matches
            matched_pain_points = []
            for pattern, original_pain in patterns["pain_points"]:
                if pattern.search(text):
                    matched_pain_points.append(original_pain)

            # Calculate confidence score
            keyword_count = len(matched_keywords)
            pain_point_count = len(matched_pain_points)

            if keyword_count == 0 and pain_point_count == 0:
                continue

            # Scoring:
            # - Each keyword match: 0.05 points (up to 0.5 for 10+ keywords)
            # - Each pain point match: 0.15 points (up to 0.45 for 3+ pain points)
            # - Sector hint match: 0.2 bonus
            keyword_score = min(0.5, keyword_count * 0.05)
            pain_point_score = min(0.45, pain_point_count * 0.15)
            sector_bonus = 0.2 if sector_hint and self._matches_sector(niche, sector_hint) else 0.0

            confidence = min(1.0, keyword_score + pain_point_score + sector_bonus)

            if confidence >= self.MIN_CONFIDENCE:
                matches.append(NicheMatch(
                    niche_id=niche.id,
                    niche_name=niche.name,
                    confidence=round(confidence, 3),
                    matched_keywords=matched_keywords[:5],  # Limit for readability
                    matched_pain_points=matched_pain_points[:3]
                ))
                total_keywords += keyword_count

        # Sort matches by confidence (highest first)
        matches.sort(key=lambda m: m.confidence, reverse=True)

        # Determine primary niche
        primary_niche = matches[0] if matches else None

        # Check if multi-niche (multiple strong matches)
        is_multi_niche = len([m for m in matches if m.confidence >= self.SECONDARY_THRESHOLD]) > 1

        return NicheDetectionResult(
            matches=matches,
            primary_niche=primary_niche,
            is_multi_niche=is_multi_niche,
            total_keywords_matched=total_keywords
        )

    def _matches_sector(self, niche, sector: str) -> bool:
        """Check if niche matches the given sector hint."""
        sector_lower = sector.lower()
        niche_lower = niche.name.lower()

        # Direct match
        if sector_lower in niche_lower or niche_lower in sector_lower:
            return True

        # Special mappings
        sector_mappings = {
            "fintech": ["financial", "finance", "banking"],
            "health": ["healthtech", "medical", "wellness"],
            "education": ["edtech", "learning"],
            "productivity": ["saas", "business"],
            "hr": ["hr_tech", "human resources"],
            "legal": ["legal_tech", "legaltech"],
            "property": ["proptech", "real estate"],
            "food": ["foodtech", "restaurant"],
            "marketing": ["martech"],
            "developer": ["devtools", "dev tools"],
        }

        for key, values in sector_mappings.items():
            if key in sector_lower and niche.id in values:
                return True
            if any(v in sector_lower for v in values) and key in niche.id:
                return True

        return False

    def get_niche_summary(self, niche_id: str) -> Optional[Dict]:
        """Get summary information about a niche.

        Args:
            niche_id: ID of the niche

        Returns:
            Dictionary with niche summary or None if not found
        """
        niche = get_niche(niche_id)
        if not niche:
            return None

        return {
            "id": niche.id,
            "name": niche.name,
            "description": niche.description,
            "market_size_billions": niche.market_size_billions,
            "growth_rate": niche.growth_rate,
            "successful_examples": niche.successful_examples[:5],
            "top_pain_points": niche.pain_points[:5],
        }

    def detect_from_opportunity_data(
        self,
        title: str,
        summary: str,
        sector: Optional[str] = None,
        product_type: Optional[str] = None
    ) -> NicheDetectionResult:
        """Detect niche from structured opportunity data.

        Args:
            title: Opportunity title
            summary: Opportunity summary
            sector: Optional sector classification
            product_type: Optional product type

        Returns:
            NicheDetectionResult
        """
        # Combine all text with weights (title matters more)
        combined_text = f"{title} {title} {summary}"

        if product_type:
            combined_text += f" {product_type}"

        return self.detect(combined_text, sector_hint=sector)
