"""App Store scheduled jobs for scraping and scoring."""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.scrapers.app_store import (
    run_app_store_scraper,
    AppStoreScraper,
    save_apps_to_db,
)
from app.services.app_scoring import AppScoringService

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def weekly_scraping_job():
    """Run weekly full App Store scraping."""
    logger.info("Starting weekly App Store scraping job...")

    try:
        async with AppStoreScraper() as scraper:
            # Scrape all categories
            apps = await scraper.scrape_all_categories(limit_per_category=100)

            if apps:
                saved_count = await save_apps_to_db(apps)
                logger.info(
                    f"Weekly scrape complete: {len(apps)} apps scraped, {saved_count} saved/updated"
                )
            else:
                logger.warning("Weekly scrape returned no apps")

    except Exception as e:
        logger.exception(f"Weekly scraping job failed: {e}")


async def trending_update_job():
    """Update trending apps and recalculate rising scores."""
    logger.info("Starting daily trending update job...")

    try:
        scoring_service = AppScoringService()
        results = await scoring_service.score_all_apps()
        logger.info(f"Trending update complete: scored {results.get('scored', 0)} apps")

    except Exception as e:
        logger.exception(f"Trending update job failed: {e}")


async def score_new_apps_job():
    """Score newly scraped apps that don't have scores yet."""
    logger.info("Scoring new unscored apps...")

    try:
        from sqlalchemy import select, func
        from app.database import get_db_context
        from app.models.app_store import AppStoreApp, AppScore

        async with get_db_context() as session:
            # Find apps without scores
            subquery = select(AppScore.app_id).distinct()

            query = (
                select(AppStoreApp.id)
                .where(~AppStoreApp.id.in_(subquery))
                .order_by(AppStoreApp.scraped_at.desc())
                .limit(100)
            )

            result = await session.execute(query)
            app_ids = [row[0] for row in result.fetchall()]

        if app_ids:
            scoring_service = AppScoringService()
            scored = 0
            for app_id in app_ids:
                try:
                    await scoring_service.score_app(app_id)
                    scored += 1
                except Exception as e:
                    logger.error(f"Error scoring app {app_id}: {e}")

            logger.info(f"New apps scored: {scored}/{len(app_ids)}")
        else:
            logger.info("No new apps to score")

    except Exception as e:
        logger.exception(f"New apps scoring job failed: {e}")


def setup_app_store_scheduler():
    """Configure and start the App Store scheduler."""
    # Weekly full scraping (Sunday at 3 AM)
    scheduler.add_job(
        weekly_scraping_job,
        CronTrigger(day_of_week="sun", hour=3, minute=0),
        id="appstore_weekly_scrape",
        name="Weekly App Store Scraping",
        replace_existing=True,
    )

    # Daily trending update (every day at 6 AM)
    scheduler.add_job(
        trending_update_job,
        CronTrigger(hour=6, minute=0),
        id="appstore_daily_trending",
        name="Daily Trending Update",
        replace_existing=True,
    )

    # New apps scoring (every 6 hours)
    scheduler.add_job(
        score_new_apps_job,
        IntervalTrigger(hours=6),
        id="appstore_score_new",
        name="Score New Apps",
        replace_existing=True,
    )

    logger.info("App Store scheduler configured")


def shutdown_app_store_scheduler():
    """Shutdown the scheduler."""
    scheduler.shutdown()
    logger.info("App Store scheduler shutdown")


if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO)

    async def test_jobs():
        """Test the jobs manually."""
        logger.info("Testing weekly scraping job...")
        await weekly_scraping_job()

        logger.info("Testing trending update job...")
        await trending_update_job()

        logger.info("Testing new apps scoring job...")
        await score_new_apps_job()

    asyncio.run(test_jobs())
