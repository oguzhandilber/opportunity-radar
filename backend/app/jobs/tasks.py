"""Background tasks for scraping and analysis.

NOTE: NOT CURRENTLY IN USE
==========================
These tasks are designed to be run as RQ background jobs but are not
currently integrated into the main application flow. The application
currently uses synchronous task execution.

See app/jobs/__init__.py for integration instructions.
"""

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def scrape_all_sources() -> dict:
    """Background job to scrape all configured sources.

    This runs the async scraping in a sync context for RQ.

    Returns:
        Dict with scraping results
    """
    from app.scheduler.jobs import daily_scrape_job

    logger.info("Starting background scrape job")

    try:
        # Run the async job in a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(daily_scrape_job())
        finally:
            loop.close()

        logger.info("Background scrape job completed")
        return {"status": "success", "message": "Scraping completed"}

    except Exception as e:
        logger.error(f"Background scrape job failed: {e}")
        return {"status": "error", "message": str(e)}


def analyze_opportunity(opportunity_id: int) -> dict:
    """Background job to run deep AI analysis on an opportunity.

    Args:
        opportunity_id: The ID of the opportunity to analyze

    Returns:
        Dict with analysis results
    """
    from app.analyzers.pipeline import deep_analyze_opportunity

    logger.info(f"Starting background analysis for opportunity {opportunity_id}")

    try:
        # Run the async analysis in a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(deep_analyze_opportunity(opportunity_id))
        finally:
            loop.close()

        if "error" in result:
            logger.error(f"Analysis failed for {opportunity_id}: {result['error']}")
            return {"status": "error", "message": result["error"]}

        logger.info(f"Background analysis completed for opportunity {opportunity_id}")
        return {"status": "success", "opportunity_id": opportunity_id, "analysis": result}

    except Exception as e:
        logger.error(f"Background analysis failed for {opportunity_id}: {e}")
        return {"status": "error", "message": str(e)}


def scrape_single_source(source_name: str) -> dict:
    """Background job to scrape a single source.

    Args:
        source_name: Name of the source to scrape (reddit, hackernews, google_trends)

    Returns:
        Dict with scraping results
    """
    logger.info(f"Starting background scrape for source: {source_name}")

    try:
        # Import scrapers dynamically
        if source_name == "reddit":
            from app.scrapers.reddit import RedditScraper
            scraper = RedditScraper()
        elif source_name == "hackernews":
            from app.scrapers.hackernews import HackerNewsScraper
            scraper = HackerNewsScraper()
        elif source_name == "google_trends":
            from app.scrapers.google_trends import GoogleTrendsScraper
            scraper = GoogleTrendsScraper()
        else:
            return {"status": "error", "message": f"Unknown source: {source_name}"}

        # Run the async scrape
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            posts = loop.run_until_complete(scraper.scrape())
        finally:
            loop.close()

        logger.info(f"Scraped {len(posts)} posts from {source_name}")
        return {
            "status": "success",
            "source": source_name,
            "posts_count": len(posts),
        }

    except Exception as e:
        logger.error(f"Background scrape failed for {source_name}: {e}")
        return {"status": "error", "message": str(e)}
