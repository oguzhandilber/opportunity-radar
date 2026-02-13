"""Tests for scraper manager."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.scrapers.manager import run_all_scrapers


class TestScraperManager:
    """Tests for scraper manager."""

    @pytest.mark.asyncio
    async def test_run_all_scrapers_success(self):
        """Test running all scrapers successfully."""
        mock_post = MagicMock()

        with (
            patch("app.scrapers.manager.HackerNewsScraper") as mock_hn,
            patch("app.scrapers.manager.GoogleTrendsScraper") as mock_gt,
            patch("app.scrapers.manager.ProductHuntScraper") as mock_ph,
            patch("app.scrapers.manager.TwitterScraper") as mock_tw,
        ):
            # Setup mocks
            for mock_class in [mock_hn, mock_gt, mock_ph, mock_tw]:
                mock_instance = MagicMock()
                mock_instance.name = "test_scraper"
                mock_instance.scrape = AsyncMock(return_value=[mock_post, mock_post])
                mock_instance.save_posts = AsyncMock()
                mock_class.return_value = mock_instance

            result = await run_all_scrapers()

            assert result["total_posts"] == 8  # 2 posts x 4 scrapers
            assert result["errors"] == []

    @pytest.mark.asyncio
    async def test_run_all_scrapers_with_errors(self):
        """Test running scrapers with some failures."""
        mock_post = MagicMock()

        with (
            patch("app.scrapers.manager.HackerNewsScraper") as mock_hn,
            patch("app.scrapers.manager.GoogleTrendsScraper") as mock_gt,
            patch("app.scrapers.manager.ProductHuntScraper") as mock_ph,
            patch("app.scrapers.manager.TwitterScraper") as mock_tw,
        ):
            # First scraper succeeds
            mock_hn_instance = MagicMock()
            mock_hn_instance.name = "hackernews"
            mock_hn_instance.scrape = AsyncMock(return_value=[mock_post])
            mock_hn_instance.save_posts = AsyncMock()
            mock_hn.return_value = mock_hn_instance

            # Second scraper fails
            mock_gt_instance = MagicMock()
            mock_gt_instance.name = "google_trends"
            mock_gt_instance.scrape = AsyncMock(side_effect=Exception("API error"))
            mock_gt.return_value = mock_gt_instance

            # Other scrapers succeed
            for mock_class in [mock_ph, mock_tw]:
                mock_instance = MagicMock()
                mock_instance.name = "test_scraper"
                mock_instance.scrape = AsyncMock(return_value=[mock_post])
                mock_instance.save_posts = AsyncMock()
                mock_class.return_value = mock_instance

            result = await run_all_scrapers()

            assert result["total_posts"] == 3  # 1 + 1 + 1 (excluding failed)
            assert len(result["errors"]) == 1
            assert result["errors"][0]["scraper"] == "google_trends"

    @pytest.mark.asyncio
    async def test_run_all_scrapers_empty_results(self):
        """Test running scrapers with empty results."""
        with (
            patch("app.scrapers.manager.HackerNewsScraper") as mock_hn,
            patch("app.scrapers.manager.GoogleTrendsScraper") as mock_gt,
            patch("app.scrapers.manager.ProductHuntScraper") as mock_ph,
            patch("app.scrapers.manager.TwitterScraper") as mock_tw,
        ):
            for mock_class in [mock_hn, mock_gt, mock_ph, mock_tw]:
                mock_instance = MagicMock()
                mock_instance.name = "test_scraper"
                mock_instance.scrape = AsyncMock(return_value=[])
                mock_instance.save_posts = AsyncMock()
                mock_class.return_value = mock_instance

            result = await run_all_scrapers()

            assert result["total_posts"] == 0
            assert result["errors"] == []
