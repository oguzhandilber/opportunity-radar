"""Tests for scheduler jobs."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestSchedulerJobs:
    """Tests for scheduler job functions."""

    @pytest.mark.asyncio
    async def test_daily_scrape_job_success(self):
        """Test daily_scrape_job runs successfully."""
        with patch("app.scrapers.manager.run_all_scrapers", new_callable=AsyncMock) as mock_scrape, \
             patch("app.analyzers.pipeline.run_analysis_pipeline", new_callable=AsyncMock) as mock_analysis:

            mock_scrape.return_value = {"total_posts": 10}
            mock_analysis.return_value = {"opportunities_created": 5}

            # Import after patching
            from app.scheduler.jobs import daily_scrape_job
            await daily_scrape_job()

            mock_scrape.assert_called_once()
            mock_analysis.assert_called_once()

    @pytest.mark.asyncio
    async def test_daily_scrape_job_handles_scraper_error(self):
        """Test daily_scrape_job handles scraper errors."""
        with patch("app.scrapers.manager.run_all_scrapers", new_callable=AsyncMock) as mock_scrape, \
             patch("app.analyzers.pipeline.run_analysis_pipeline", new_callable=AsyncMock) as mock_analysis:

            mock_scrape.side_effect = Exception("Scraper failed")

            from app.scheduler.jobs import daily_scrape_job
            # Should not raise, just log the error
            await daily_scrape_job()

            mock_scrape.assert_called_once()
            # Analysis won't be called if scraper fails first (due to exception)
            mock_analysis.assert_not_called()

    @pytest.mark.asyncio
    async def test_daily_scrape_job_handles_analysis_error(self):
        """Test daily_scrape_job handles analysis errors."""
        with patch("app.scrapers.manager.run_all_scrapers", new_callable=AsyncMock) as mock_scrape, \
             patch("app.analyzers.pipeline.run_analysis_pipeline", new_callable=AsyncMock) as mock_analysis:

            mock_scrape.return_value = {"total_posts": 5}
            mock_analysis.side_effect = Exception("Analysis failed")

            from app.scheduler.jobs import daily_scrape_job
            # Should not raise, just log the error
            await daily_scrape_job()

            mock_scrape.assert_called_once()
            mock_analysis.assert_called_once()


class TestSchedulerSetup:
    """Tests for scheduler setup functions."""

    def test_setup_scheduler(self):
        """Test setup_scheduler configures jobs."""
        from app.scheduler.jobs import setup_scheduler, scheduler

        with patch.object(scheduler, "add_job") as mock_add_job, \
             patch.object(scheduler, "start") as mock_start:

            setup_scheduler()

            mock_add_job.assert_called_once()
            mock_start.assert_called_once()

            # Check job was configured correctly
            call_kwargs = mock_add_job.call_args[1]
            assert call_kwargs["id"] == "daily_scrape"
            assert call_kwargs["replace_existing"] is True

    def test_shutdown_scheduler(self):
        """Test shutdown_scheduler stops scheduler."""
        from app.scheduler.jobs import shutdown_scheduler, scheduler

        with patch.object(scheduler, "shutdown") as mock_shutdown:
            shutdown_scheduler()

            mock_shutdown.assert_called_once_with(wait=False)

    def test_scheduler_instance_exists(self):
        """Test scheduler instance is created."""
        from app.scheduler.jobs import scheduler
        from apscheduler.schedulers.asyncio import AsyncIOScheduler

        assert scheduler is not None
        assert isinstance(scheduler, AsyncIOScheduler)
