"""Google Trends scraper using pytrends."""

import asyncio
import logging
from datetime import datetime, timezone

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import get_settings
from app.scrapers.base import BaseScraper, ScrapedPost

logger = logging.getLogger(__name__)
settings = get_settings()

# Regions to monitor
REGIONS = [
    ("US", "united_states"),
    ("TR", "turkey"),
    ("GB", "united_kingdom"),
]

# Seed keywords for related queries
SEED_KEYWORDS = ["saas", "startup", "app", "automation", "ai tool"]


class GoogleTrendsScraper(BaseScraper):
    """Scraper for Google Trends using pytrends."""

    name = "google_trends"

    def __init__(self):
        self._rate_limit_delay = max(1.0, settings.request_delay_seconds)

    async def scrape(self) -> list[ScrapedPost]:
        """Scrape trending topics from Google Trends."""
        loop = asyncio.get_event_loop()
        posts = await loop.run_in_executor(None, self._scrape_sync)
        return posts

    def _scrape_sync(self) -> list[ScrapedPost]:
        """Synchronous scraping logic."""
        try:
            from pytrends.request import TrendReq
        except ImportError:
            logger.error("pytrends not installed. Run: pip install pytrends")
            return []

        posts = []
        logger.info(f"Starting Google Trends scrape for {len(REGIONS)} regions")

        try:
            pytrends = TrendReq(hl="en-US", tz=360, timeout=(10, 25))
        except Exception as e:
            logger.error(f"Failed to initialize pytrends: {e}")
            return []

        # Get trending searches for each region
        for geo_code, geo_name in REGIONS:
            try:
                posts.extend(self._fetch_trending_searches(pytrends, geo_code, geo_name))
                import time
                time.sleep(self._rate_limit_delay)
            except Exception as e:
                logger.error(f"Error getting trends for {geo_code}: {e}")
                continue

        # Get related queries for seed keywords
        for keyword in SEED_KEYWORDS:
            try:
                posts.extend(self._fetch_related_queries(pytrends, keyword))
                import time
                time.sleep(self._rate_limit_delay)
            except Exception as e:
                logger.error(f"Error getting related queries for {keyword}: {e}")
                continue

        logger.info(f"Google Trends scrape complete: {len(posts)} items found")
        return posts

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        before_sleep=lambda retry_state: logger.warning(
            f"Google Trends retry attempt {retry_state.attempt_number} after error"
        ),
    )
    def _fetch_trending_searches(self, pytrends, geo_code: str, geo_name: str) -> list[ScrapedPost]:
        """Fetch trending searches for a region."""
        posts = []

        try:
            trending = pytrends.trending_searches(pn=geo_name)

            for idx, row in trending.iterrows():
                keyword = row[0]
                posts.append(
                    ScrapedPost(
                        source=self.name,
                        external_id=f"{geo_code}_{keyword}_{datetime.now(timezone.utc).strftime('%Y%m%d')}",
                        content=f"Trending in {geo_code}: {keyword}",
                        author=None,
                        url=f"https://trends.google.com/trends/explore?q={keyword}&geo={geo_code}",
                        engagement=0,
                        created_at=datetime.now(timezone.utc),
                    )
                )

            if posts:
                logger.debug(f"Found {len(posts)} trending searches for {geo_code}")

        except Exception as e:
            error_str = str(e).lower()
            if "429" in error_str or "rate" in error_str:
                logger.warning(f"Rate limited for {geo_code}, skipping")
            else:
                raise

        return posts

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        before_sleep=lambda retry_state: logger.warning(
            f"Google Trends retry attempt {retry_state.attempt_number} after error"
        ),
    )
    def _fetch_related_queries(self, pytrends, keyword: str) -> list[ScrapedPost]:
        """Fetch related rising queries for a keyword."""
        posts = []

        try:
            pytrends.build_payload([keyword], timeframe="now 7-d")
            related = pytrends.related_queries()

            if keyword in related and related[keyword]["rising"] is not None:
                rising_df = related[keyword]["rising"]
                for idx, row in rising_df.head(10).iterrows():
                    query = row["query"]
                    value = row["value"] if row["value"] else 0

                    posts.append(
                        ScrapedPost(
                            source=self.name,
                            external_id=f"related_{keyword}_{query}_{datetime.now(timezone.utc).strftime('%Y%m%d')}",
                            content=f"Rising search related to '{keyword}': {query} (growth: {value}%)",
                            author=None,
                            url=f"https://trends.google.com/trends/explore?q={query}",
                            engagement=int(value) if value else 0,
                            created_at=datetime.now(timezone.utc),
                        )
                    )

                if posts:
                    logger.debug(f"Found {len(posts)} rising queries for '{keyword}'")

        except Exception as e:
            error_str = str(e).lower()
            if "429" in error_str or "rate" in error_str:
                logger.warning(f"Rate limited for keyword '{keyword}', skipping")
            else:
                raise

        return posts

    def test(self) -> str:
        """Test pytrends connection."""
        try:
            from pytrends.request import TrendReq

            pytrends = TrendReq(hl="en-US", tz=360, timeout=(5, 10))
            trending = pytrends.trending_searches(pn="united_states")

            if len(trending) > 0:
                logger.info("Google Trends connection test successful")
                return f"{self.name} scraper: Connected successfully ({len(trending)} trends found)"

            return f"{self.name} scraper: Connected but no trends returned"

        except ImportError:
            logger.error("pytrends not installed")
            return f"{self.name} scraper: pytrends not installed. Run: pip install pytrends"
        except Exception as e:
            logger.error(f"Google Trends connection failed: {e}")
            return f"{self.name} scraper: Connection failed - {e}"
