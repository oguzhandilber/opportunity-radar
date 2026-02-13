"""Scraper manager - orchestrates all scrapers."""

import logging

from app.scrapers.base import BaseScraper
from app.scrapers.reddit import RedditScraper
from app.scrapers.hackernews import HackerNewsScraper
from app.scrapers.google_trends import GoogleTrendsScraper
from app.scrapers.product_hunt import ProductHuntScraper
from app.scrapers.twitter import TwitterScraper
from app.scrapers.linkedin import LinkedInScraper
from app.scrapers.indiehackers import IndieHackersScraper
from app.scrapers.github import GitHubTrendingScraper
from app.scrapers.tiktok import TikTokScraper
from app.scrapers.youtube import YouTubeScraper
from app.analyzers.deduplicator import deduplicate_raw_posts
from app.database import get_db_context

logger = logging.getLogger(__name__)


async def run_all_scrapers() -> dict:
    """Run all scrapers and collect results."""
    scrapers: list[BaseScraper] = [
        RedditScraper(),
        HackerNewsScraper(),
        GoogleTrendsScraper(),
        ProductHuntScraper(),
        TwitterScraper(),
        LinkedInScraper(),
        IndieHackersScraper(),
        GitHubTrendingScraper(),
        TikTokScraper(),
        YouTubeScraper(),
    ]

    total_posts = 0
    total_after_dedup = 0
    errors = []

    for scraper in scrapers:
        try:
            posts = await scraper.scrape()
            original_count = len(posts)

            # Deduplicate within the batch
            async with get_db_context() as session:
                unique_posts = await deduplicate_raw_posts(
                    session, posts, threshold=0.7
                )

            dedup_count = len(unique_posts)
            duplicates_removed = original_count - dedup_count

            if duplicates_removed > 0:
                logger.info(
                    f"{scraper.name}: Removed {duplicates_removed} duplicate posts"
                )

            await scraper.save_posts(unique_posts)
            total_posts += original_count
            total_after_dedup += dedup_count

        except Exception as e:
            errors.append({"scraper": scraper.name, "error": str(e)})
            logger.error(f"Error in {scraper.name}: {e}")

    logger.info(
        f"Scraping complete: {total_posts} total -> {total_after_dedup} after dedup"
    )

    return {
        "total_posts": total_posts,
        "unique_posts": total_after_dedup,
        "duplicates_removed": total_posts - total_after_dedup,
        "errors": errors,
    }
