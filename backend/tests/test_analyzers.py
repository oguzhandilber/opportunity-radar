"""Tests for analyzers (classifier, enricher, scorer)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.analyzers.classifier import OpportunityClassifier, CLASSIFICATION_PROMPT
from app.analyzers.enricher import OpportunityEnricher, ENRICHMENT_PROMPT
from app.analyzers.scorer import OpportunityScorer, SCORING_PROMPT


class TestOpportunityClassifier:
    """Tests for OpportunityClassifier."""

    def test_classification_prompt_exists(self):
        """Test that classification prompt is defined."""
        assert CLASSIFICATION_PROMPT is not None
        assert "is_opportunity" in CLASSIFICATION_PROMPT
        assert "title" in CLASSIFICATION_PROMPT

    @pytest.mark.asyncio
    async def test_classify_success(self):
        """Test successful classification."""
        with patch("app.analyzers.classifier.get_ai_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.complete_json = AsyncMock(return_value={
                "is_opportunity": True,
                "title": "AI Writing Assistant",
                "summary": "A tool to help with writing",
                "product_type": "SaaS",
                "sector": "Productivity",
                "business_model": "Subscription",
            })
            mock_get_client.return_value = mock_client

            classifier = OpportunityClassifier()
            result = await classifier.classify("I wish there was an AI writing tool")

            assert result is not None
            assert result["title"] == "AI Writing Assistant"
            assert result["product_type"] == "SaaS"

    @pytest.mark.asyncio
    async def test_classify_not_opportunity(self):
        """Test classification when content is not an opportunity."""
        with patch("app.analyzers.classifier.get_ai_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.complete_json = AsyncMock(return_value={
                "is_opportunity": False,
                "title": None,
            })
            mock_get_client.return_value = mock_client

            classifier = OpportunityClassifier()
            result = await classifier.classify("Just a regular post about nothing")

            assert result is None

    @pytest.mark.asyncio
    async def test_classify_error_handling(self):
        """Test classification error handling."""
        with patch("app.analyzers.classifier.get_ai_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.complete_json = AsyncMock(side_effect=Exception("API error"))
            mock_get_client.return_value = mock_client

            classifier = OpportunityClassifier()
            result = await classifier.classify("Test content")

            assert result is None

    @pytest.mark.asyncio
    async def test_classify_truncates_long_content(self):
        """Test that long content is truncated."""
        with patch("app.analyzers.classifier.get_ai_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.complete_json = AsyncMock(return_value={"is_opportunity": False})
            mock_get_client.return_value = mock_client

            classifier = OpportunityClassifier()
            long_content = "x" * 5000
            await classifier.classify(long_content)

            # Check that the prompt was called with truncated content
            call_args = mock_client.complete_json.call_args[0][0]
            assert len(call_args) < 5000


class TestOpportunityEnricher:
    """Tests for OpportunityEnricher."""

    def test_enrichment_prompt_exists(self):
        """Test that enrichment prompt is defined."""
        assert ENRICHMENT_PROMPT is not None
        assert "competitors" in ENRICHMENT_PROMPT
        assert "suggested_features" in ENRICHMENT_PROMPT

    @pytest.mark.asyncio
    async def test_enrich_success(self):
        """Test successful enrichment."""
        with patch("app.analyzers.enricher.get_ai_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.complete_json = AsyncMock(return_value={
                "competitors": [
                    {"name": "Competitor A", "url": "https://a.com", "notes": "Similar product"}
                ],
                "suggested_features": [
                    {"feature": "Auto-save", "priority": "high", "description": "Save automatically"}
                ],
                "go_to_market": "Launch on Product Hunt and target indie developers.",
            })
            mock_get_client.return_value = mock_client

            enricher = OpportunityEnricher()
            classification = {
                "title": "AI Tool",
                "summary": "An AI tool",
                "product_type": "SaaS",
                "sector": "Tech",
                "business_model": "Subscription",
            }
            result = await enricher.enrich("Test content", classification)

            assert len(result["competitors"]) == 1
            assert result["competitors"][0]["name"] == "Competitor A"
            assert len(result["suggested_features"]) == 1
            assert "Product Hunt" in result["go_to_market"]

    @pytest.mark.asyncio
    async def test_enrich_with_none_classification(self):
        """Test enrichment with None classification."""
        with patch("app.analyzers.enricher.get_ai_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.complete_json = AsyncMock(return_value={
                "competitors": [],
                "suggested_features": [],
                "go_to_market": "Strategy here",
            })
            mock_get_client.return_value = mock_client

            enricher = OpportunityEnricher()
            result = await enricher.enrich("Test content", None)

            assert "go_to_market" in result

    @pytest.mark.asyncio
    async def test_enrich_error_handling(self):
        """Test enrichment error handling."""
        with patch("app.analyzers.enricher.get_ai_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.complete_json = AsyncMock(side_effect=Exception("API error"))
            mock_get_client.return_value = mock_client

            enricher = OpportunityEnricher()
            result = await enricher.enrich("Test content", {})

            # Should return empty defaults on error
            assert result["competitors"] == []
            assert result["suggested_features"] == []
            assert result["go_to_market"] == ""


class TestOpportunityScorer:
    """Tests for OpportunityScorer."""

    def test_scoring_prompt_exists(self):
        """Test that scoring prompt is defined."""
        assert SCORING_PROMPT is not None
        assert "demand_score" in SCORING_PROMPT
        assert "market_score" in SCORING_PROMPT

    @pytest.mark.asyncio
    async def test_score_success(self):
        """Test successful scoring."""
        with patch("app.analyzers.scorer.get_ai_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.complete_json = AsyncMock(return_value={
                "demand_score": 8,
                "market_score": 7,
                "feasibility_score": 9,
                "revenue_score": 6,
                "total_score": 7.5,
                "confidence": 0.8,
            })
            mock_get_client.return_value = mock_client

            scorer = OpportunityScorer()
            classification = {
                "title": "AI Tool",
                "summary": "An AI tool",
                "product_type": "SaaS",
                "sector": "Tech",
                "business_model": "Subscription",
            }
            result = await scorer.score("Test content", classification)

            assert result["demand_score"] == 8
            assert result["total_score"] == 7.5
            assert result["confidence"] == 0.8

    @pytest.mark.asyncio
    async def test_score_calculates_total_when_missing(self):
        """Test that total score is calculated when not provided."""
        with patch("app.analyzers.scorer.get_ai_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.complete_json = AsyncMock(return_value={
                "demand_score": 8,
                "market_score": 6,
                "feasibility_score": 8,
                "revenue_score": 6,
                "total_score": None,  # Not provided
                "confidence": 0.7,
            })
            mock_get_client.return_value = mock_client

            scorer = OpportunityScorer()
            result = await scorer.score("Test content", {})

            # Should calculate weighted average
            assert result["total_score"] is not None
            assert 6 <= result["total_score"] <= 8

    @pytest.mark.asyncio
    async def test_score_with_none_classification(self):
        """Test scoring with None classification."""
        with patch("app.analyzers.scorer.get_ai_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.complete_json = AsyncMock(return_value={
                "demand_score": 5,
                "market_score": 5,
                "feasibility_score": 5,
                "revenue_score": 5,
                "total_score": 5,
                "confidence": 0.5,
            })
            mock_get_client.return_value = mock_client

            scorer = OpportunityScorer()
            result = await scorer.score("Test content", None)

            assert result["total_score"] == 5

    @pytest.mark.asyncio
    async def test_score_error_handling(self):
        """Test scoring error handling."""
        with patch("app.analyzers.scorer.get_ai_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.complete_json = AsyncMock(side_effect=Exception("API error"))
            mock_get_client.return_value = mock_client

            scorer = OpportunityScorer()
            result = await scorer.score("Test content", {})

            # Should return default scores on error
            assert result["demand_score"] == 5
            assert result["market_score"] == 5
            assert result["total_score"] == 5
            assert result["confidence"] == 0.3
