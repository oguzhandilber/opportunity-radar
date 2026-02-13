"""Scheduler for automated scraping jobs."""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

scheduler = AsyncIOScheduler()


async def daily_scrape_job():
    """Run daily scraping and analysis job."""
    from app.scrapers.manager import run_all_scrapers
    from app.analyzers.pipeline import run_analysis_pipeline

    logger.info("Starting daily scrape job...")

    try:
        # Run scrapers
        scrape_results = await run_all_scrapers()
        logger.info(f"Scraped {scrape_results.get('total_posts', 0)} posts")

        # Run analysis
        analysis_results = await run_analysis_pipeline()
        logger.info(f"Created {analysis_results.get('opportunities_created', 0)} opportunities")

    except Exception as e:
        logger.exception(f"Daily scrape job failed: {e}")


def setup_scheduler():
    """Configure and start the scheduler."""
    # Run daily at 6 AM
    scheduler.add_job(
        daily_scrape_job,
        CronTrigger(hour=6, minute=0),
        id="daily_scrape",
        name="Daily Opportunity Scraper",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler started - daily scrape at 6:00 AM")


def shutdown_scheduler():
    """Shutdown the scheduler."""
    scheduler.shutdown(wait=False)
    logger.info("Scheduler shut down")
