"""Tests for historical success validation (Pivot 4)."""

import pytest

from app.analyzers.success_patterns import (
    SuccessPatternDatabase,
    SuccessPattern,
    Category,
    OutcomeType,
)
from app.analyzers.pattern_matcher import PatternMatcher, PatternMatchResult
from app.analyzers.success_predictor import SuccessPredictor, SuccessPrediction


class TestSuccessPatternDatabase:
    """Tests for SuccessPatternDatabase."""

    def setup_method(self):
        self.db = SuccessPatternDatabase()

    def test_has_minimum_patterns(self):
        """Test database has at least 30 patterns."""
        patterns = self.db.get_all_patterns()
        assert len(patterns) >= 30

    def test_patterns_have_required_fields(self):
        """Test all patterns have required fields."""
        for pattern in self.db.get_all_patterns():
            assert pattern.name
            assert pattern.category in Category
            assert pattern.original_pain
            assert pattern.solution_type
            assert pattern.outcome in OutcomeType
            assert pattern.outcome_value
            assert pattern.year_founded > 2000
            assert len(pattern.signals) > 0
            assert pattern.target_audience
            assert pattern.key_differentiator

    def test_get_by_category(self):
        """Test getting patterns by category."""
        communication = self.db.get_by_category(Category.COMMUNICATION)
        assert len(communication) >= 3
        for pattern in communication:
            assert pattern.category == Category.COMMUNICATION

    def test_get_all_signals(self):
        """Test getting all unique signals."""
        signals = self.db.get_all_signals()
        assert len(signals) > 50
        assert "email" in signals
        assert "api" in signals

    def test_search_by_signals(self):
        """Test searching patterns by signals."""
        results = self.db.search_by_signals(["email", "chat", "team"])
        assert len(results) > 0
        # Slack should be in results
        slack_result = next((p for p, _ in results if p.name == "Slack"), None)
        assert slack_result is not None

    def test_search_by_signals_empty(self):
        """Test searching with no matching signals."""
        results = self.db.search_by_signals(["xyznonexistent123"])
        assert len(results) == 0


class TestPatternMatcher:
    """Tests for PatternMatcher."""

    def setup_method(self):
        self.matcher = PatternMatcher()

    def test_match_communication_opportunity(self):
        """Test matching a communication-related opportunity."""
        text = """
        I'm frustrated with email overload at my company. We need a better way
        for the team to communicate without sending hundreds of emails a day.
        Looking for a chat solution.
        """
        result = self.matcher.match(text)

        assert result.matches
        assert result.overall_score > 0
        # Should match Slack or similar
        names = [m.pattern.name for m in result.matches]
        assert "Slack" in names or "Discord" in names or "Intercom" in names

    def test_match_scheduling_opportunity(self):
        """Test matching a scheduling-related opportunity."""
        text = """
        Scheduling meetings is such a pain. There's so much back and forth
        over email trying to find a time that works. I need a simpler way
        to share my calendar availability.
        """
        result = self.matcher.match(text)

        assert result.matches
        # Should match Calendly
        names = [m.pattern.name for m in result.matches]
        assert "Calendly" in names

    def test_match_design_opportunity(self):
        """Test matching a design-related opportunity."""
        text = """
        Our design team struggles to collaborate on mockups. We're constantly
        sending Sketch files back and forth and losing track of versions.
        Need real-time collaboration for UI design.
        """
        result = self.matcher.match(text)

        assert result.matches
        # Should match Figma
        names = [m.pattern.name for m in result.matches]
        assert "Figma" in names or "Miro" in names

    def test_match_developer_tools(self):
        """Test matching a developer tools opportunity."""
        text = """
        Integrating payment processing is a nightmare. The APIs are terrible
        and documentation is outdated. We need a developer-friendly payment API.
        """
        result = self.matcher.match(text)

        assert result.matches
        # Should match Stripe
        names = [m.pattern.name for m in result.matches]
        assert "Stripe" in names or "Twilio" in names

    def test_match_no_clear_pattern(self):
        """Test matching text with no clear pattern."""
        text = "I like pizza and watching movies on weekends."
        result = self.matcher.match(text)

        assert result.overall_score < 3

    def test_match_empty_text(self):
        """Test matching empty text."""
        result = self.matcher.match("")

        assert not result.matches
        assert result.overall_score == 0
        assert result.best_match is None

    def test_match_returns_top_5(self):
        """Test that match returns at most 5 results."""
        text = """
        We need better tools for project management, team communication,
        scheduling meetings, tracking tasks, managing workflows, design collaboration,
        code deployment, payment processing, and analytics.
        """
        result = self.matcher.match(text)

        assert len(result.matches) <= 5

    def test_similar_successes_list(self):
        """Test similar_successes returns company names."""
        text = "Team chat and messaging for workplace communication"
        result = self.matcher.match(text)

        assert isinstance(result.similar_successes, list)
        for name in result.similar_successes:
            assert isinstance(name, str)


class TestSuccessPredictor:
    """Tests for SuccessPredictor."""

    def setup_method(self):
        self.predictor = SuccessPredictor()

    def test_predict_high_success_opportunity(self):
        """Test predicting high success opportunity."""
        text = """
        I'm canceling my Asana subscription ($50/month) because it's too slow.
        Looking for a simpler project management tool. Willing to pay up to $100/month
        for something that actually works for my team.
        """
        result = self.predictor.predict(text)

        assert result.success_likelihood >= 50
        assert result.confidence > 0
        assert result.risk_level in ["low", "medium"]
        assert "pattern_match" in result.factors
        assert "payment_intent" in result.factors

    def test_predict_low_success_opportunity(self):
        """Test predicting low success opportunity."""
        text = "I wish there was a better way to do things."
        result = self.predictor.predict(text)

        assert result.success_likelihood < 50
        assert result.risk_level in ["medium", "high"]

    def test_predict_empty_text(self):
        """Test predicting with empty text."""
        result = self.predictor.predict("")

        assert result.success_likelihood == 0
        assert result.confidence == 0
        assert result.risk_level == "high"

    def test_predict_with_precomputed(self):
        """Test predicting with pre-computed results."""
        from app.analyzers.payment_signals import PaymentSignalDetector
        from app.analyzers.competitor_extractor import CompetitorExtractor
        from app.analyzers.journey_classifier import JourneyClassifier
        from app.analyzers.pattern_matcher import PatternMatcher

        text = "Looking for a team chat solution to replace email"

        # Pre-compute some results
        payment_result = PaymentSignalDetector().detect(text)
        pattern_result = PatternMatcher().match(text)

        result = self.predictor.predict(
            text,
            pre_computed={
                "payment_result": payment_result,
                "pattern_result": pattern_result,
            }
        )

        assert result.success_likelihood >= 0
        assert result.factors

    def test_prediction_factors_are_normalized(self):
        """Test that prediction factors are in valid range."""
        text = "Need a better scheduling tool for meetings"
        result = self.predictor.predict(text)

        for factor, value in result.factors.items():
            assert 0 <= value <= 100, f"{factor} out of range: {value}"

    def test_recommendation_text(self):
        """Test recommendation text is generated."""
        text = "Looking for project management software"
        result = self.predictor.predict(text)

        assert result.recommendation
        assert isinstance(result.recommendation, str)
        assert len(result.recommendation) > 10

    def test_similar_successes_returned(self):
        """Test similar successes are returned."""
        text = "Team messaging and collaboration platform"
        result = self.predictor.predict(text)

        assert isinstance(result.similar_successes, list)


class TestSuccessValidationIntegration:
    """Integration tests for success validation."""

    def setup_method(self):
        self.matcher = PatternMatcher()
        self.predictor = SuccessPredictor()

    def test_full_pipeline_high_intent(self):
        """Test full pipeline with high intent opportunity."""
        text = """
        I'm paying $200/month for Salesforce but it's way too complex for our
        small sales team. Looking for a simpler CRM that focuses on the basics.
        We just need to track leads and deals without all the enterprise features.
        Already tried HubSpot but their pricing is confusing.
        """

        # Pattern matching
        pattern_result = self.matcher.match(text)
        assert pattern_result.matches
        assert "Salesforce" in text or pattern_result.overall_score > 0

        # Success prediction
        prediction = self.predictor.predict(text)
        assert prediction.success_likelihood >= 40
        assert prediction.factors["payment_intent"] > 50
        assert prediction.risk_level != "high"

    def test_full_pipeline_novel_idea(self):
        """Test full pipeline with novel idea (no pattern match)."""
        text = """
        I want to build an app that uses quantum computing to predict
        the optimal time to water houseplants based on cosmic radiation levels.
        """

        pattern_result = self.matcher.match(text)
        prediction = self.predictor.predict(text)

        # Novel ideas should have low success likelihood
        assert prediction.success_likelihood < 50
        assert prediction.risk_level == "high"
        # Low payment intent for vague ideas
        assert prediction.factors["payment_intent"] < 30

    def test_category_distribution(self):
        """Test patterns cover diverse categories."""
        db = SuccessPatternDatabase()
        categories_found = set()

        for pattern in db.get_all_patterns():
            categories_found.add(pattern.category)

        # Should have at least 10 different categories
        assert len(categories_found) >= 10

    def test_outcome_distribution(self):
        """Test patterns have diverse outcomes."""
        db = SuccessPatternDatabase()
        outcomes_found = set()

        for pattern in db.get_all_patterns():
            outcomes_found.add(pattern.outcome)

        # Should have multiple outcome types
        assert len(outcomes_found) >= 3
