"""Tests for background jobs."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock


class TestJobQueue:
    """Tests for job queue functionality."""

    def test_is_redis_available_false_when_not_running(self):
        """Test redis availability check when Redis is not running."""
        from app.jobs.queue import is_redis_available

        with patch("app.jobs.queue.get_redis") as mock_get_redis:
            mock_redis = MagicMock()
            mock_redis.ping.side_effect = Exception("Connection refused")
            mock_get_redis.return_value = mock_redis

            result = is_redis_available()
            assert result is False

    def test_is_redis_available_true_when_running(self):
        """Test redis availability check when Redis is running."""
        from app.jobs.queue import is_redis_available

        with patch("app.jobs.queue.get_redis") as mock_get_redis:
            mock_redis = MagicMock()
            mock_redis.ping.return_value = True
            mock_get_redis.return_value = mock_redis

            result = is_redis_available()
            assert result is True

    def test_get_job_status_not_found(self):
        """Test getting status of non-existent job."""
        from app.jobs.queue import get_job_status

        with patch("app.jobs.queue.get_redis") as mock_get_redis:
            with patch("rq.job.Job.fetch") as mock_fetch:
                mock_fetch.side_effect = Exception("Job not found")

                result = get_job_status("nonexistent-id")

                assert result["status"] == "not_found"
                assert "error" in result


class TestJobTasks:
    """Tests for background task functions."""

    def test_scrape_all_sources_success(self):
        """Test scrape_all_sources task."""
        from app.jobs.tasks import scrape_all_sources

        with patch("app.scheduler.jobs.daily_scrape_job", new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = None

            result = scrape_all_sources()

            assert result["status"] == "success"
            mock_scrape.assert_called_once()

    def test_scrape_all_sources_error(self):
        """Test scrape_all_sources task handles errors."""
        from app.jobs.tasks import scrape_all_sources

        with patch("app.scheduler.jobs.daily_scrape_job", new_callable=AsyncMock) as mock_scrape:
            mock_scrape.side_effect = Exception("Scrape failed")

            result = scrape_all_sources()

            assert result["status"] == "error"
            assert "Scrape failed" in result["message"]

    def test_analyze_opportunity_success(self):
        """Test analyze_opportunity task."""
        from app.jobs.tasks import analyze_opportunity

        with patch("app.analyzers.pipeline.deep_analyze_opportunity", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = {"result": "analysis data"}

            result = analyze_opportunity(123)

            assert result["status"] == "success"
            assert result["opportunity_id"] == 123
            mock_analyze.assert_called_once_with(123)

    def test_analyze_opportunity_error(self):
        """Test analyze_opportunity task handles errors."""
        from app.jobs.tasks import analyze_opportunity

        with patch("app.analyzers.pipeline.deep_analyze_opportunity", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = {"error": "Analysis failed"}

            result = analyze_opportunity(123)

            assert result["status"] == "error"

    def test_scrape_single_source_reddit(self):
        """Test scraping single source (reddit)."""
        from app.jobs.tasks import scrape_single_source

        with patch("app.scrapers.reddit.RedditScraper") as mock_scraper_class:
            mock_scraper = MagicMock()
            mock_scraper.scrape = AsyncMock(return_value=[MagicMock(), MagicMock()])
            mock_scraper_class.return_value = mock_scraper

            result = scrape_single_source("reddit")

            assert result["status"] == "success"
            assert result["source"] == "reddit"
            assert result["posts_count"] == 2

    def test_scrape_single_source_unknown(self):
        """Test scraping unknown source returns error."""
        from app.jobs.tasks import scrape_single_source

        result = scrape_single_source("unknown_source")

        assert result["status"] == "error"
        assert "Unknown source" in result["message"]

    def test_scrape_single_source_hackernews(self):
        """Test scraping HackerNews source."""
        from app.jobs.tasks import scrape_single_source

        with patch("app.scrapers.hackernews.HackerNewsScraper") as mock_scraper_class:
            mock_scraper = MagicMock()
            mock_scraper.scrape = AsyncMock(return_value=[])
            mock_scraper_class.return_value = mock_scraper

            result = scrape_single_source("hackernews")

            assert result["status"] == "success"
            assert result["source"] == "hackernews"

    def test_scrape_single_source_google_trends(self):
        """Test scraping Google Trends source."""
        from app.jobs.tasks import scrape_single_source

        with patch("app.scrapers.google_trends.GoogleTrendsScraper") as mock_scraper_class:
            mock_scraper = MagicMock()
            mock_scraper.scrape = AsyncMock(return_value=[])
            mock_scraper_class.return_value = mock_scraper

            result = scrape_single_source("google_trends")

            assert result["status"] == "success"
            assert result["source"] == "google_trends"
