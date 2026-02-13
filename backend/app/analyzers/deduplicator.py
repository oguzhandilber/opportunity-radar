"""Content similarity deduplication for opportunities.

Uses text similarity to detect and merge similar opportunities,
preventing duplicate ideas from cluttering the database.
"""

import hashlib
import re
from dataclasses import dataclass


# Common stop words to filter out
STOP_WORDS = {
    "a",
    "an",
    "the",
    "and",
    "or",
    "but",
    "in",
    "on",
    "at",
    "to",
    "for",
    "of",
    "with",
    "by",
    "from",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "will",
    "would",
    "could",
    "should",
    "may",
    "might",
    "must",
    "can",
    "this",
    "that",
    "these",
    "those",
    "i",
    "you",
    "he",
    "she",
    "it",
    "we",
    "they",
    "my",
    "your",
    "his",
    "her",
    "its",
    "our",
    "their",
    "what",
    "which",
    "who",
    "whom",
    "where",
    "when",
    "why",
    "how",
    "all",
    "each",
    "every",
    "both",
    "few",
    "more",
    "most",
    "other",
    "some",
    "such",
    "no",
    "not",
    "only",
    "same",
    "so",
    "than",
    "too",
    "very",
    "just",
    "also",
    "now",
    "here",
    "there",
    "then",
    "if",
    "because",
    "as",
    "until",
    "while",
    "about",
    "into",
    "through",
    "during",
    "before",
    "after",
    "above",
    "below",
    "up",
    "down",
    "out",
    "off",
    "over",
    "under",
    "again",
    "further",
    "any",
    "am",
    "im",
    "ive",
    "dont",
    "doesnt",
    "didnt",
    "cant",
    "wont",
    "looking",
    "need",
    "want",
    "anyone",
    "anything",
    "something",
    "someone",
}


@dataclass
class SimilarityResult:
    """Result of similarity comparison."""

    is_similar: bool
    similarity_score: float
    matched_id: int | None = None


def normalize_text(text: str) -> str:
    """Normalize text for comparison."""
    if not text:
        return ""
    # Lowercase
    text = text.lower()
    # Remove URLs
    text = re.sub(r"https?://\S+", "", text)
    # Remove special characters, keep alphanumeric and spaces
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def get_keywords(text: str) -> set[str]:
    """Extract meaningful keywords from text (removing stop words)."""
    words = text.split()
    return {w for w in words if w not in STOP_WORDS and len(w) > 2}


def get_shingles(text: str, k: int = 2) -> set[str]:
    """Get k-shingles (word n-grams) from text."""
    words = [w for w in text.split() if w not in STOP_WORDS and len(w) > 2]
    if len(words) < k:
        return set(words) if words else set()
    shingles = set()
    # Add individual words
    shingles.update(words)
    # Add bigrams
    for i in range(len(words) - 1):
        shingles.add(f"{words[i]} {words[i + 1]}")
    return shingles


def jaccard_similarity(set1: set, set2: set) -> float:
    """Calculate Jaccard similarity between two sets."""
    if not set1 or not set2:
        return 0.0
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0


def content_hash(text: str) -> str:
    """Generate a hash for normalized content."""
    normalized = normalize_text(text)
    return hashlib.md5(normalized.encode()).hexdigest()


def extract_key_concepts(text: str) -> set[str]:
    """Extract key domain concepts that indicate the core idea."""
    normalized = normalize_text(text)

    # Important domain keywords to look for
    domain_keywords = {
        "app",
        "tool",
        "software",
        "platform",
        "service",
        "saas",
        "api",
        "invoice",
        "invoicing",
        "payment",
        "billing",
        "subscription",
        "crm",
        "erp",
        "cms",
        "ecommerce",
        "marketplace",
        "automation",
        "workflow",
        "integration",
        "dashboard",
        "analytics",
        "tracking",
        "management",
        "scheduling",
        "booking",
        "calendar",
        "email",
        "marketing",
        "seo",
        "social",
        "media",
        "content",
        "learning",
        "education",
        "course",
        "training",
        "language",
        "spanish",
        "english",
        "french",
        "health",
        "fitness",
        "nutrition",
        "meditation",
        "wellness",
        "gym",
        "workout",
        "finance",
        "budget",
        "accounting",
        "investing",
        "trading",
        "banking",
        "money",
        "project",
        "task",
        "team",
        "collaboration",
        "remote",
        "hr",
        "hiring",
        "recruiting",
        "ai",
        "ml",
        "chatbot",
        "assistant",
        "recommendation",
        "gpt",
        "llm",
        "podcast",
        "video",
        "audio",
        "streaming",
        "music",
        "photo",
        "image",
        "recipe",
        "cooking",
        "food",
        "restaurant",
        "delivery",
        "grocery",
        "travel",
        "booking",
        "hotel",
        "flight",
        "vacation",
        "trip",
        "freelance",
        "freelancer",
        "contractor",
        "client",
        "agency",
        "inventory",
        "warehouse",
        "shipping",
        "logistics",
        "supply",
        "database",
        "storage",
        "backup",
        "security",
        "privacy",
        "encryption",
    }

    words = set(normalized.split())
    return words & domain_keywords


class ContentDeduplicator:
    """Detects and handles similar content/opportunities."""

    def __init__(self, similarity_threshold: float = 0.4):
        """
        Initialize deduplicator.

        Args:
            similarity_threshold: Minimum similarity to consider as duplicate (0.0-1.0)
        """
        self.similarity_threshold = similarity_threshold
        self._content_cache: dict[
            int, tuple[str, set[str], set[str]]
        ] = {}  # id -> (normalized, shingles, concepts)

    def add_to_cache(self, opportunity_id: int, content: str) -> None:
        """Add content to the comparison cache."""
        normalized = normalize_text(content)
        shingles = get_shingles(normalized)
        concepts = extract_key_concepts(normalized)
        self._content_cache[opportunity_id] = (normalized, shingles, concepts)

    def clear_cache(self) -> None:
        """Clear the content cache."""
        self._content_cache.clear()

    def find_similar(self, content) -> SimilarityResult:
        """
        Find if content is similar to any cached content.

        Returns:
            SimilarityResult with match info if found
        """
        # Defensive: ensure content is a string
        if not isinstance(content, str):
            if isinstance(content, dict):
                # If dict, try to get 'content' key or stringify
                content = str(content.get("content", str(content)))
            else:
                content = str(content)

        normalized = normalize_text(content)
        new_shingles = get_shingles(normalized)
        new_concepts = extract_key_concepts(normalized)

        best_match_id = None
        best_score = 0.0

        for opp_id, (
            cached_norm,
            cached_shingles,
            cached_concepts,
        ) in self._content_cache.items():
            # Quick check: exact match
            if normalized == cached_norm:
                return SimilarityResult(
                    is_similar=True, similarity_score=1.0, matched_id=opp_id
                )

            # Calculate similarity using multiple signals
            shingle_sim = jaccard_similarity(new_shingles, cached_shingles)
            concept_sim = (
                jaccard_similarity(new_concepts, cached_concepts)
                if new_concepts and cached_concepts
                else 0
            )

            # Weighted combination: concepts are more important
            if new_concepts and cached_concepts:
                score = 0.6 * shingle_sim + 0.4 * concept_sim
            else:
                score = shingle_sim

            if score > best_score:
                best_score = score
                best_match_id = opp_id

        is_similar = best_score >= self.similarity_threshold

        return SimilarityResult(
            is_similar=is_similar,
            similarity_score=best_score,
            matched_id=best_match_id if is_similar else None,
        )

    def check_similarity(self, content1: str, content2: str) -> float:
        """
        Check similarity between two pieces of content.

        Returns:
            Similarity score (0.0-1.0)
        """
        norm1 = normalize_text(content1)
        norm2 = normalize_text(content2)

        shingles1 = get_shingles(norm1)
        shingles2 = get_shingles(norm2)

        concepts1 = extract_key_concepts(norm1)
        concepts2 = extract_key_concepts(norm2)

        shingle_sim = jaccard_similarity(shingles1, shingles2)
        concept_sim = (
            jaccard_similarity(concepts1, concepts2) if concepts1 and concepts2 else 0
        )

        if concepts1 and concepts2:
            return 0.6 * shingle_sim + 0.4 * concept_sim
        return shingle_sim


async def find_duplicate_opportunities(
    session, content: str, threshold: float = 0.6, limit: int = 100
) -> list[tuple[int, float]]:
    """
    Find opportunities in database that are similar to given content.

    Args:
        session: Database session
        content: Content to compare
        threshold: Minimum similarity threshold
        limit: Max number of recent opportunities to check

    Returns:
        List of (opportunity_id, similarity_score) tuples
    """
    from sqlalchemy import select
    from app.database import Opportunity

    # Get recent opportunities
    query = (
        select(Opportunity.id, Opportunity.title, Opportunity.summary)
        .order_by(Opportunity.created_at.desc())
        .limit(limit)
    )

    result = await session.execute(query)
    opportunities = result.all()

    deduplicator = ContentDeduplicator(threshold)

    # Build cache from existing opportunities
    for opp_id, title, summary in opportunities:
        combined = f"{title or ''} {summary or ''}"
        deduplicator.add_to_cache(opp_id, combined)

    # Find similar
    similar_result = deduplicator.find_similar(content)

    if similar_result.is_similar:
        return [(similar_result.matched_id, similar_result.similarity_score)]

    return []


async def deduplicate_raw_posts(session, posts: list, threshold: float = 0.7) -> list:
    """
    Filter out duplicate posts before processing.

    Args:
        session: Database session
        posts: List of ScrapedPost objects
        threshold: Similarity threshold

    Returns:
        Filtered list with duplicates removed
    """
    if not posts:
        return posts

    deduplicator = ContentDeduplicator(threshold)
    unique_posts = []

    for post in posts:
        similar = deduplicator.find_similar(post.content)

        if not similar.is_similar:
            unique_posts.append(post)
            # Add to cache for future comparisons within this batch
            deduplicator.add_to_cache(id(post), post.content)

    return unique_posts
