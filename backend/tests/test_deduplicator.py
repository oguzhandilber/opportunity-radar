"""Tests for content deduplication."""

import pytest
from app.analyzers.deduplicator import (
    ContentDeduplicator,
    normalize_text,
    get_shingles,
    get_keywords,
    jaccard_similarity,
    extract_key_concepts,
)


class TestNormalizeText:
    """Tests for text normalization."""

    def test_lowercase(self):
        """Test that text is lowercased."""
        assert normalize_text("HELLO WORLD") == "hello world"

    def test_removes_urls(self):
        """Test that URLs are removed."""
        text = "Check out https://example.com for more info"
        result = normalize_text(text)
        assert "https://example.com" not in result
        assert "check out" in result

    def test_removes_special_chars(self):
        """Test that special characters are removed."""
        text = "Hello, World! How's it going?"
        result = normalize_text(text)
        assert "," not in result
        assert "!" not in result
        assert "'" not in result

    def test_collapses_whitespace(self):
        """Test that multiple spaces are collapsed."""
        text = "Hello    World   Test"
        result = normalize_text(text)
        assert "  " not in result

    def test_empty_string(self):
        """Test handling of empty string."""
        assert normalize_text("") == ""
        assert normalize_text(None) == ""


class TestGetShingles:
    """Tests for shingle extraction."""

    def test_extracts_words(self):
        """Test that individual words are extracted."""
        text = "invoice tool payment"
        shingles = get_shingles(text)
        assert "invoice" in shingles
        assert "tool" in shingles
        assert "payment" in shingles

    def test_extracts_bigrams(self):
        """Test that bigrams are extracted."""
        text = "invoice tool payment"
        shingles = get_shingles(text)
        assert "invoice tool" in shingles
        assert "tool payment" in shingles

    def test_filters_stop_words(self):
        """Test that stop words are filtered."""
        text = "i need a tool for the invoices"
        shingles = get_shingles(text)
        assert "need" not in shingles  # stop word
        assert "the" not in shingles  # stop word
        assert "tool" in shingles
        assert "invoices" in shingles


class TestJaccardSimilarity:
    """Tests for Jaccard similarity."""

    def test_identical_sets(self):
        """Test that identical sets have similarity 1.0."""
        set1 = {"a", "b", "c"}
        assert jaccard_similarity(set1, set1) == 1.0

    def test_disjoint_sets(self):
        """Test that disjoint sets have similarity 0.0."""
        set1 = {"a", "b", "c"}
        set2 = {"d", "e", "f"}
        assert jaccard_similarity(set1, set2) == 0.0

    def test_partial_overlap(self):
        """Test partial overlap."""
        set1 = {"a", "b", "c"}
        set2 = {"b", "c", "d"}
        # Intersection: {b, c} = 2, Union: {a, b, c, d} = 4
        assert jaccard_similarity(set1, set2) == 0.5

    def test_empty_sets(self):
        """Test empty sets."""
        assert jaccard_similarity(set(), set()) == 0.0
        assert jaccard_similarity({"a"}, set()) == 0.0


class TestExtractKeyConcepts:
    """Tests for key concept extraction."""

    def test_extracts_domain_keywords(self):
        """Test that domain keywords are extracted."""
        text = "need an invoice tool for payment tracking"
        concepts = extract_key_concepts(text)
        assert "invoice" in concepts
        assert "tool" in concepts
        assert "payment" in concepts
        assert "tracking" in concepts

    def test_ignores_non_domain_words(self):
        """Test that non-domain words are ignored."""
        text = "hello world random words here"
        concepts = extract_key_concepts(text)
        assert len(concepts) == 0


class TestContentDeduplicator:
    """Tests for ContentDeduplicator class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.dedup = ContentDeduplicator(similarity_threshold=0.4)

    def test_add_to_cache(self):
        """Test adding content to cache."""
        self.dedup.add_to_cache(1, "Test content")
        assert 1 in self.dedup._content_cache

    def test_clear_cache(self):
        """Test clearing cache."""
        self.dedup.add_to_cache(1, "Test content")
        self.dedup.clear_cache()
        assert len(self.dedup._content_cache) == 0

    def test_find_similar_exact_match(self):
        """Test finding exact match."""
        self.dedup.add_to_cache(1, "Need an invoicing tool")
        result = self.dedup.find_similar("Need an invoicing tool")
        assert result.is_similar is True
        assert result.similarity_score == 1.0
        assert result.matched_id == 1

    def test_find_similar_no_match(self):
        """Test when no similar content exists."""
        self.dedup.add_to_cache(1, "Need an invoicing tool")
        result = self.dedup.find_similar("Best podcast app for music")
        assert result.is_similar is False
        assert result.matched_id is None

    def test_find_similar_with_variations(self):
        """Test finding similar content with variations."""
        self.dedup.add_to_cache(1, "I need a tool to manage my invoices and track payments")
        self.dedup.add_to_cache(2, "Looking for a CRM solution for small business")

        # Similar to invoice content
        result = self.dedup.find_similar("Need invoicing tool to track my payments")
        assert result.is_similar is True
        assert result.matched_id == 1

        # Similar to CRM content
        result2 = self.dedup.find_similar("I am looking for a CRM for my small business")
        assert result2.is_similar is True
        assert result2.matched_id == 2

    def test_check_similarity(self):
        """Test direct similarity check between two contents."""
        content1 = "Need an invoicing tool for payments"
        content2 = "Need invoicing tool for payment tracking"

        score = self.dedup.check_similarity(content1, content2)
        assert 0 <= score <= 1
        assert score > 0.1  # Should have some similarity due to overlapping words

    def test_threshold_respected(self):
        """Test that similarity threshold is respected."""
        high_threshold_dedup = ContentDeduplicator(similarity_threshold=0.9)
        high_threshold_dedup.add_to_cache(1, "Invoice management software")

        result = high_threshold_dedup.find_similar("Invoicing tool")
        # With high threshold, should not match
        assert result.is_similar is False


class TestDeduplicatorIntegration:
    """Integration tests for deduplication."""

    def test_batch_deduplication(self):
        """Test deduplicating a batch of content."""
        dedup = ContentDeduplicator(similarity_threshold=0.4)

        contents = [
            "Need an invoice tool",
            "Looking for invoicing software",  # Similar to first
            "Best CRM for startups",
            "CRM solution for small business",  # Similar to third
            "Podcast app recommendations",  # Different
        ]

        unique_contents = []
        for i, content in enumerate(contents):
            result = dedup.find_similar(content)
            if not result.is_similar:
                unique_contents.append(content)
                dedup.add_to_cache(i, content)

        # Should have filtered duplicates
        assert len(unique_contents) < len(contents)
        assert len(unique_contents) >= 3  # At least 3 unique concepts
