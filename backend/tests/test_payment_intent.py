"""Tests for payment intent analyzers (Pivot 3)."""

import pytest

from app.analyzers.payment_signals import PaymentSignalDetector, PaymentSignalResult
from app.analyzers.price_extractor import PriceExtractor, PriceExtractionResult
from app.analyzers.competitor_extractor import CompetitorExtractor, CompetitorSentiment
from app.analyzers.journey_classifier import JourneyClassifier, JourneyStage


class TestPaymentSignalDetector:
    """Tests for PaymentSignalDetector."""

    def setup_method(self):
        self.detector = PaymentSignalDetector()

    def test_tier1_currently_paying(self):
        """Test Tier 1: Currently paying detection."""
        text = "I'm paying $50/month for this garbage tool and it still doesn't work"
        result = self.detector.detect(text)

        assert result.has_signal is True
        assert result.tier == 1
        assert result.strength >= 0.9
        assert len(result.matches) > 0

    def test_tier1_spending_monthly(self):
        """Test Tier 1: Spending monthly detection."""
        text = "We spend $200 per month on analytics tools"
        result = self.detector.detect(text)

        assert result.has_signal is True
        assert result.tier == 1

    def test_tier2_willing_to_pay(self):
        """Test Tier 2: Willing to pay detection."""
        text = "I would pay $100 for a tool that actually works"
        result = self.detector.detect(text)

        assert result.has_signal is True
        assert result.tier == 2
        assert result.strength >= 0.7

    def test_tier2_ready_to_buy(self):
        """Test Tier 2: Ready to buy detection."""
        text = "I'm ready to pay for a solution, just need to find the right one"
        result = self.detector.detect(text)

        assert result.has_signal is True
        assert result.tier == 2

    def test_tier3_canceling_subscription(self):
        """Test Tier 3: Canceling subscription detection."""
        text = "I'm canceling my Asana subscription, looking for alternatives"
        result = self.detector.detect(text)

        assert result.has_signal is True
        assert result.tier == 3

    def test_tier3_switching_from(self):
        """Test Tier 3: Switching from detection."""
        text = "Switching from Notion because it's too slow"
        result = self.detector.detect(text)

        assert result.has_signal is True
        assert result.tier == 3

    def test_tier4_too_expensive(self):
        """Test Tier 4: Too expensive detection."""
        text = "This tool costs too much for what it does"
        result = self.detector.detect(text)

        assert result.has_signal is True
        assert result.tier == 4

    def test_tier4_price_mention(self):
        """Test Tier 4: Price mention detection."""
        text = "Looking for something priced at $10/month or less"
        result = self.detector.detect(text)

        assert result.has_signal is True
        assert result.tier == 4

    def test_no_signal(self):
        """Test no payment signal detection."""
        text = "This is a great tutorial about Python programming"
        result = self.detector.detect(text)

        assert result.has_signal is False
        assert result.tier is None
        assert result.strength == 0.0

    def test_empty_text(self):
        """Test empty text handling."""
        result = self.detector.detect("")

        assert result.has_signal is False
        assert result.tier is None

    def test_multiple_signals_takes_best(self):
        """Test multiple signals take the best tier."""
        text = "I'm paying $50/month for Slack but I'd pay more for something better"
        result = self.detector.detect(text)

        # Should be Tier 1 (currently paying) not Tier 2 (would pay)
        assert result.tier == 1


class TestPriceExtractor:
    """Tests for PriceExtractor."""

    def setup_method(self):
        self.extractor = PriceExtractor()

    def test_extract_simple_price(self):
        """Test simple price extraction."""
        text = "Looking for a tool under $50"
        result = self.extractor.extract(text)

        assert len(result.prices) == 1
        assert result.prices[0].amount == 50
        assert result.prices[0].currency == "$"

    def test_extract_monthly_price(self):
        """Test monthly price extraction."""
        text = "I pay $29/month for this service"
        result = self.extractor.extract(text)

        assert len(result.prices) == 1
        assert result.prices[0].amount == 29
        assert result.prices[0].period == "month"
        assert result.monthly_equivalent == 29

    def test_extract_yearly_price(self):
        """Test yearly price extraction with monthly conversion."""
        text = "The annual plan is $120/year"
        result = self.extractor.extract(text)

        assert len(result.prices) == 1
        assert result.prices[0].amount == 120
        assert result.prices[0].period == "year"
        assert result.monthly_equivalent == 10.0  # 120/12

    def test_extract_k_notation(self):
        """Test K notation price extraction."""
        text = "Our budget is $5k per year"
        result = self.extractor.extract(text)

        # May match both patterns (k notation and regular)
        assert len(result.prices) >= 1
        # Should have the 5000 amount from k notation
        amounts = [p.amount for p in result.prices]
        assert 5000 in amounts

    def test_extract_multiple_prices(self):
        """Test multiple price extraction."""
        text = "Prices range from $10/month to $100/month"
        result = self.extractor.extract(text)

        assert len(result.prices) >= 2
        assert result.min_price == 10
        assert result.max_price == 100

    def test_price_type_budget(self):
        """Test price type detection for budget."""
        text = "My budget is $500 for this project"
        result = self.extractor.extract(text)

        assert len(result.prices) == 1
        assert result.prices[0].price_type == "budget"

    def test_price_type_current_spend(self):
        """Test price type detection for current spend."""
        text = "We're currently paying $200/month"
        result = self.extractor.extract(text)

        assert len(result.prices) == 1
        assert result.prices[0].price_type == "current_spend"

    def test_empty_text(self):
        """Test empty text handling."""
        result = self.extractor.extract("")

        assert len(result.prices) == 0
        assert result.min_price is None
        assert result.max_price is None

    def test_no_prices(self):
        """Test text with no prices."""
        text = "Looking for a project management tool"
        result = self.extractor.extract(text)

        assert len(result.prices) == 0


class TestCompetitorExtractor:
    """Tests for CompetitorExtractor."""

    def setup_method(self):
        self.extractor = CompetitorExtractor()

    def test_extract_single_competitor(self):
        """Test single competitor extraction."""
        text = "I'm using Slack for team communication"
        result = self.extractor.extract(text)

        assert result.competitors_count == 1
        assert result.mentions[0].name == "slack"
        assert result.mentions[0].category == "communication"

    def test_extract_multiple_competitors(self):
        """Test multiple competitor extraction."""
        text = "Comparing Asana vs Trello for project management"
        result = self.extractor.extract(text)

        assert result.competitors_count == 2
        assert "project_management" in result.categories

    def test_churning_detection(self):
        """Test churning from competitor detection."""
        text = "I'm leaving Notion because it's too slow"
        result = self.extractor.extract(text)

        assert result.has_churning is True
        assert "notion" in result.churning_from
        assert result.mentions[0].sentiment == CompetitorSentiment.CHURNING

    def test_negative_sentiment(self):
        """Test negative sentiment detection."""
        text = "Slack is buggy and unreliable"
        result = self.extractor.extract(text)

        assert result.mentions[0].sentiment == CompetitorSentiment.NEGATIVE

    def test_positive_sentiment(self):
        """Test positive sentiment detection."""
        text = "I absolutely love Notion, it's amazing"
        result = self.extractor.extract(text)

        assert result.mentions[0].sentiment == CompetitorSentiment.POSITIVE

    def test_neutral_sentiment(self):
        """Test neutral sentiment detection."""
        text = "Trello is a project management tool"
        result = self.extractor.extract(text)

        assert result.mentions[0].sentiment == CompetitorSentiment.NEUTRAL

    def test_empty_text(self):
        """Test empty text handling."""
        result = self.extractor.extract("")

        assert result.competitors_count == 0
        assert len(result.mentions) == 0

    def test_no_competitors(self):
        """Test text with no competitors."""
        text = "I need a tool for managing my tasks"
        result = self.extractor.extract(text)

        assert result.competitors_count == 0

    def test_category_detection(self):
        """Test correct category detection."""
        text = "Using Stripe for payments and Mixpanel for analytics"
        result = self.extractor.extract(text)

        assert result.competitors_count == 2
        assert "payments" in result.categories
        assert "analytics" in result.categories


class TestJourneyClassifier:
    """Tests for JourneyClassifier."""

    def setup_method(self):
        self.classifier = JourneyClassifier()

    def test_churning_stage(self):
        """Test churning stage classification."""
        text = "I'm leaving Asana, need something better"
        result = self.classifier.classify(text)

        assert result.stage == JourneyStage.CHURNING
        assert result.conversion_potential == "high"
        assert result.confidence >= 0.8

    def test_ready_stage(self):
        """Test ready to buy stage classification."""
        text = "Ready to pay for a good solution, where can I sign up?"
        result = self.classifier.classify(text)

        assert result.stage == JourneyStage.READY
        assert result.conversion_potential == "high"

    def test_considering_stage(self):
        """Test considering stage classification."""
        text = "Comparing different options, which is the best tool?"
        result = self.classifier.classify(text)

        assert result.stage == JourneyStage.CONSIDERING
        assert result.conversion_potential == "medium"

    def test_aware_stage(self):
        """Test aware stage classification."""
        text = "I wish there was a better way to manage my tasks"
        result = self.classifier.classify(text)

        assert result.stage == JourneyStage.AWARE
        assert result.conversion_potential == "low"

    def test_unaware_stage(self):
        """Test unaware stage classification."""
        text = "Python is a great programming language"
        result = self.classifier.classify(text)

        assert result.stage == JourneyStage.UNAWARE
        assert result.conversion_potential == "very_low"

    def test_empty_text(self):
        """Test empty text handling."""
        result = self.classifier.classify("")

        assert result.stage == JourneyStage.UNAWARE
        assert result.confidence == 0.0

    def test_multiple_signals_priority(self):
        """Test that higher value stages take priority."""
        text = "I wish there was a tool, and I'm ready to pay for it"
        result = self.classifier.classify(text)

        # READY should take priority over AWARE
        assert result.stage == JourneyStage.READY

    def test_recommended_action(self):
        """Test recommended action for each stage."""
        churning = self.classifier.classify("Leaving Slack because it sucks")
        action = self.classifier.get_recommended_action(churning.stage)

        assert "immediate" in action.lower() or "outreach" in action.lower()


class TestPaymentIntentIntegration:
    """Integration tests for all payment intent analyzers."""

    def setup_method(self):
        self.payment_detector = PaymentSignalDetector()
        self.price_extractor = PriceExtractor()
        self.competitor_extractor = CompetitorExtractor()
        self.journey_classifier = JourneyClassifier()

    def test_high_intent_opportunity(self):
        """Test high intent opportunity detection."""
        text = """
        I'm canceling my Asana subscription ($25/month) because it's too slow.
        Looking for something better, willing to pay up to $50/month.
        Anyone have recommendations?
        """

        payment = self.payment_detector.detect(text)
        prices = self.price_extractor.extract(text)
        competitors = self.competitor_extractor.extract(text)
        journey = self.journey_classifier.classify(text)

        # Should have payment signal (tier 2 or 3)
        assert payment.has_signal is True
        assert payment.tier in [1, 2, 3]

        # Should have price mentions
        assert len(prices.prices) >= 1
        assert prices.has_recurring is True

        # Should detect Asana as churning
        assert competitors.has_churning is True
        assert "asana" in competitors.churning_from

        # Should be in high-intent stage
        assert journey.stage in [JourneyStage.CHURNING, JourneyStage.READY, JourneyStage.CONSIDERING]

    def test_low_intent_post(self):
        """Test low intent post detection."""
        text = "I wish there was a better way to do this, but whatever."

        payment = self.payment_detector.detect(text)
        prices = self.price_extractor.extract(text)
        competitors = self.competitor_extractor.extract(text)
        journey = self.journey_classifier.classify(text)

        # Low or no payment signals
        assert payment.tier is None or payment.tier >= 4

        # No price mentions
        assert len(prices.prices) == 0

        # No competitors
        assert competitors.competitors_count == 0

        # Low stage
        assert journey.stage in [JourneyStage.AWARE, JourneyStage.UNAWARE]
