"""App Store scraper using iTunes RSS Feed and Search API."""

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx
from bs4 import BeautifulSoup

from app.config import get_settings
from app.models.app_store import (
    AppStoreApp,
    AppStoreCategory,
    AppTrendHistory,
    CATEGORY_REVENUE_BENCHMARKS,
    CATEGORY_COMPLEXITY,
)
from app.database import get_db_context

logger = logging.getLogger(__name__)

settings = get_settings()

# iTunes RSS Feed endpoints
ITUNES_RSS_BASE = "https://itunes.apple.com/us/rss"

# App Store categories with RSS feed IDs
CATEGORY_RSS_IDS = {
    "Business": "6014",
    "Productivity": "6007",
    "Finance": "6015",
    "Health & Fitness": "6013",
    "Medical": "6012",
    "Education": "6016",
    "Food & Drink": "6010",
    "Shopping": "6022",
    "Social Networking": "6005",
    "Sports": "6006",
    "Music": "6011",
    "Navigation": "6018",
    "Utilities": "6002",
    "Weather": "6001",
    "Lifestyle": "6012",
}

# Content type filters
CONTENT_TYPES = {
    "topfreeapplications": "Free Apps",
    "toppaidapplications": "Paid Apps",
    "topgrossingapplications": "Top Grossing",
}


class AppStoreScraper:
    """Scrape App Store data using iTunes RSS and API."""

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
        )
        self.base_url = "https://itunes.apple.com"
        self.lookup_url = "https://itunes.apple.com"
        self.rss_url = "https://itunes.apple.com/us/rss"

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def scrape_category(
        self,
        category_name: str,
        content_type: str = "topfreeapplications",
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        category_id = CATEGORY_RSS_IDS.get(category_name)
        if not category_id:
            logger.warning(f"Unknown category: {category_name}")
            return []

        url = f"{self.base_url}/search"
        params = {
            "term": category_name,
            "country": "us",
            "media": "software",
            "entity": "software",
            "limit": limit,
        }

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            apps = []
            for result in data.get("results", []):
                app = self._parse_search_result(result)
                if app:
                    apps.append(app)

            logger.info(f"Scraped {len(apps)} apps from {category_name}")
            return apps

        except Exception as e:
            logger.error(f"Error scraping {category_name}: {e}")
            return []

    def _parse_rss_entry(
        self, entry: Dict, category_name: str
    ) -> Optional[Dict[str, Any]]:
        """Parse a single RSS entry into app data."""
        try:
            # Extract basic info
            app_id = entry.get("id", {}).get("attributes", {}).get("im:id")
            if not app_id:
                return None

            name = entry.get("im:name", {}).get("label", "Unknown")
            developer = entry.get("im:artist", {}).get("label", "Unknown")
            icon_url = entry.get("im:image", [{}])[-1].get("label", "")
            app_store_url = entry.get("id", {}).get("label", "")

            # Price
            price_info = entry.get("im:price", {}).get("attributes", {})
            price = float(price_info.get("amount", 0)) if price_info else 0.0

            # Category
            category_label = (
                entry.get("category", {})
                .get("attributes", {})
                .get("term", category_name)
            )

            # Release date
            release_date_str = entry.get("im:releaseDate", {}).get("label", "")
            release_date = None
            if release_date_str:
                try:
                    release_date = datetime.fromisoformat(
                        release_date_str.replace("Z", "+00:00")
                    )
                except ValueError:
                    pass

            # Rating (if available)
            rating_info = entry.get("im:rating", {})
            content_rating = rating_info.get("attributes", {}).get("type", "")

            return {
                "apple_app_id": app_id,
                "name": name,
                "developer": developer,
                "icon_url": icon_url,
                "app_store_url": app_store_url,
                "price": price,
                "category_name": category_label,
                "content_rating": content_rating,
                "release_date": release_date,
            }

        except Exception as e:
            logger.error(f"Error parsing RSS entry: {e}")
            return None

    def _parse_lookup_result(self, result: Dict) -> Optional[Dict[str, Any]]:
        """Parse a lookup API result into app data."""
        try:
            app_id = str(result.get("trackId"))
            if not app_id:
                return None

            return {
                "apple_app_id": app_id,
                "name": result.get("trackName", "Unknown"),
                "developer": result.get("artistName", "Unknown"),
                "description": result.get("description", ""),
                "icon_url": result.get(
                    "artworkUrl512", result.get("artworkUrl100", "")
                ),
                "screenshot_urls": result.get("screenshotUrls", []),
                "app_store_url": result.get("trackViewUrl", ""),
                "price": result.get("price", 0.0),
                "currency": result.get("currency", "USD"),
                "rating": result.get("averageUserRating", 0.0),
                "rating_count": result.get("userRatingCount", 0),
                "current_rating_count": result.get(
                    "userRatingCountForCurrentVersion", 0
                ),
                "category_name": result.get("primaryGenreName", "Unknown"),
                "content_rating": result.get("contentAdvisoryRating", ""),
                "supported_devices": result.get("supportedDevices", []),
                "languages": result.get("languageCodesISO2A", []),
                "release_date": result.get("releaseDate", ""),
                "last_updated": result.get("currentVersionReleaseDate", ""),
            }

        except Exception as e:
            logger.error(f"Error parsing lookup result: {e}")
            return None

    async def get_app_details(
        self, app_id: str, country: str = "us"
    ) -> Optional[Dict[str, Any]]:
        """Get detailed app information from iTunes API."""
        url = f"{self.lookup_url}/{country}/lookup"
        params = {"id": app_id}

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            results = data.get("results", [])
            if not results:
                return None

            return self._parse_lookup_result(results[0])

        except Exception as e:
            logger.error(f"Error fetching app details for {app_id}: {e}")
            return None

    async def search_apps(
        self, term: str, country: str = "us", limit: int = 25
    ) -> List[Dict[str, Any]]:
        """Search for apps using iTunes Search API."""
        url = f"{self.base_url}/search"
        params = {
            "term": term,
            "country": country,
            "media": "software",
            "entity": "software",
            "limit": limit,
        }

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            apps = []
            for result in data.get("results", []):
                app = self._parse_search_result(result)
                if app:
                    apps.append(app)

            return apps

        except Exception as e:
            logger.error(f"Search error for '{term}': {e}")
            return []

    def _parse_search_result(self, result: Dict) -> Optional[Dict[str, Any]]:
        """Parse a search result into app data."""
        try:
            app_id = str(result.get("trackId"))
            if not app_id:
                return None

            return {
                "apple_app_id": app_id,
                "name": result.get("trackName", "Unknown"),
                "developer": result.get("artistName", "Unknown"),
                "description": result.get("description", ""),
                "icon_url": result.get(
                    "artworkUrl512", result.get("artworkUrl100", "")
                ),
                "app_store_url": result.get("trackViewUrl", ""),
                "price": result.get("price", 0.0),
                "currency": result.get("currency", "USD"),
                "rating": result.get("averageUserRating", 0.0),
                "rating_count": result.get("userRatingCount", 0),
                "current_rating_count": result.get(
                    "userRatingCountForCurrentVersion", 0
                ),
                "category_name": result.get("primaryGenreName", "Unknown"),
                "content_rating": result.get("contentAdvisoryRating", ""),
                "supported_devices": result.get("supportedDevices", []),
                "languages": result.get("languageCodesISO2A", []),
                "release_date": result.get("releaseDate", ""),
                "last_updated": result.get("currentVersionReleaseDate", ""),
            }

        except Exception as e:
            logger.error(f"Error parsing search result: {e}")
            return None

    async def scrape_all_categories(
        self, limit_per_category: int = 100
    ) -> List[Dict[str, Any]]:
        """Scrape top apps from all configured categories."""
        all_apps = []

        for category_name in CATEGORY_RSS_IDS.keys():
            try:
                # Scrape free apps
                free_apps = await self.scrape_category(
                    category_name, "topfreeapplications", limit_per_category
                )
                all_apps.extend(free_apps)

                # Small delay to respect rate limits
                await asyncio.sleep(0.5)

                # Scrape top grossing for additional apps
                grossing_apps = await self.scrape_category(
                    category_name, "topgrossingapplications", limit_per_category // 2
                )
                all_apps.extend(grossing_apps)

                await asyncio.sleep(0.5)

            except Exception as e:
                logger.error(f"Error scraping category {category_name}: {e}")

        logger.info(f"Total apps scraped: {len(all_apps)}")
        return all_apps


async def save_apps_to_db(apps: List[Dict[str, Any]]) -> int:
    """Save scraped apps to database, updating existing ones."""
    saved_count = 0

    async with get_db_context() as session:
        for app_data in apps:
            # Find or create category
            category_name = app_data.pop("category_name", "Unknown")
            from sqlalchemy import select

            cat_query = select(AppStoreCategory).where(
                AppStoreCategory.name == category_name
            )
            result = await session.execute(cat_query)
            category = result.scalar_one_or_none()

            if not category:
                # Create category if doesn't exist
                category = AppStoreCategory(
                    name=category_name,
                    apple_id=CATEGORY_RSS_IDS.get(category_name, "0000"),
                    revenue_benchmark=CATEGORY_REVENUE_BENCHMARKS.get(
                        category_name, 20.0
                    ),
                    complexity_multiplier=CATEGORY_COMPLEXITY.get(category_name, 0.5),
                )
                session.add(category)
                await session.flush()

            # Find or create app
            app_id = app_data.get("apple_app_id")
            if not app_id:
                continue

            query = select(AppStoreApp).where(AppStoreApp.apple_app_id == app_id)
            result = await session.execute(query)
            existing_app = result.scalar_one_or_none()

            if existing_app:
                # Update existing app
                for key, value in app_data.items():
                    if hasattr(existing_app, key) and key != "apple_app_id":
                        setattr(existing_app, key, value)
                existing_app.scraped_at = datetime.now(timezone.utc)
            else:
                # Create new app
                app = AppStoreApp(
                    category_id=category.id,
                    scraped_at=datetime.now(timezone.utc),
                    **app_data,
                )
                session.add(app)

            saved_count += 1

        await session.commit()

    return saved_count


async def run_app_store_scraper():
    """Main entry point for the App Store scraper."""
    logger.info("Starting App Store scraper...")

    async with AppStoreScraper() as scraper:
        # Scrape all categories
        apps = await scraper.scrape_all_categories(limit_per_category=100)

        # Save to database
        saved_count = await save_apps_to_db(apps)

        logger.info(f"App Store scraper completed. Saved {saved_count} apps.")


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) > 1 and sys.argv[1] == "--scrape":
        asyncio.run(run_app_store_scraper())
