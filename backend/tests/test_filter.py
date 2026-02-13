"""Tests for content filter."""

import pytest

from app.analyzers.filter import ContentFilter


class TestContentFilter:
    """Tests for ContentFilter class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.filter = ContentFilter()

    def test_short_content_filtered(self):
        """Test that short content is filtered out."""
        assert not self.filter.is_relevant("Too short")

    def test_spam_content_filtered(self):
        """Test that spam content is filtered out."""
        spam_content = "Buy now! Limited time offer! Click here for amazing deals! " * 3
        assert not self.filter.is_relevant(spam_content)

    def test_irrelevant_content_filtered(self):
        """Test that irrelevant content is filtered out."""
        meme_content = "This is so funny lol lmao! " * 5
        assert not self.filter.is_relevant(meme_content)

    def test_opportunity_content_passes(self):
        """Test that content with opportunity signals passes."""
        good_content = """
        I've been looking for a tool that can help me automate my
        email marketing workflow. I'm frustrated with the current
        solutions and would pay for something better. The market
        for this seems to be growing.
        """
        assert self.filter.is_relevant(good_content)

    def test_startup_idea_passes(self):
        """Test that startup idea content passes."""
        idea_content = """
        I have an idea for a SaaS product that helps small businesses
        manage their inventory. There's a market opportunity here
        because current solutions are too expensive.
        """
        assert self.filter.is_relevant(idea_content)

    def test_crypto_spam_filtered(self):
        """Test that crypto spam is filtered."""
        crypto_spam = "Bitcoin giveaway! Ethereum airdrop coming soon! " * 3
        assert not self.filter.is_relevant(crypto_spam)

    def test_clean_content_removes_urls(self):
        """Test that clean_content removes URLs."""
        content = "Check out https://example.com for more info and www.test.com too"
        cleaned = self.filter.clean_content(content)
        assert "https://example.com" not in cleaned
        assert "www.test.com" not in cleaned
        assert "[URL]" in cleaned

    def test_clean_content_removes_whitespace(self):
        """Test that clean_content normalizes whitespace."""
        content = "Too    many     spaces\n\n\nand newlines"
        cleaned = self.filter.clean_content(content)
        assert "    " not in cleaned
        assert "\n" not in cleaned
