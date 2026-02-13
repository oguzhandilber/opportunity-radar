"""Hacker News scraper using Algolia API."""

import logging

import httpx
from datetime import datetime

from app.scrapers.base import BaseScraper, ScrapedPost
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Algolia HN Search API
ALGOLIA_API_URL = "https://hn.algolia.com/api/v1"


class HackerNewsScraper(BaseScraper):
    """Scraper for Hacker News using Algolia Search API."""

    name = "hackernews"

    async def scrape(self) -> list[ScrapedPost]:
        """Scrape posts from Hacker News."""
        posts = []

        async with httpx.AsyncClient() as client:
            # Scrape Show HN posts
            show_posts = await self._search_hn(client, "Show HN")
            posts.extend(show_posts)

            # Scrape Ask HN posts
            ask_posts = await self._search_hn(client, "Ask HN")
            posts.extend(ask_posts)

            # Scrape opportunity keywords
            for keyword in ["looking for", "need a tool", "wish there was"]:
                keyword_posts = await self._search_hn(client, keyword)
                posts.extend(keyword_posts)

        return posts

    async def _search_hn(
        self, client: httpx.AsyncClient, query: str
    ) -> list[ScrapedPost]:
        """Search Hacker News via Algolia API."""
        posts = []

        try:
            response = await client.get(
                f"{ALGOLIA_API_URL}/search",
                params={
                    "query": query,
                    "tags": "story",
                    "hitsPerPage": 20,
                },
            )
            response.raise_for_status()
            data = response.json()

            for hit in data.get("hits", []):
                content = hit.get("title", "")
                if hit.get("story_text"):
                    content += f"\n\n{hit['story_text']}"

                posts.append(
                    ScrapedPost(
                        source=self.name,
                        external_id=str(hit.get("objectID")),
                        content=content,
                        author=hit.get("author"),
                        url=hit.get("url")
                        or f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                        engagement=hit.get("points", 0) + hit.get("num_comments", 0),
                        created_at=datetime.fromtimestamp(hit.get("created_at_i", 0)),
                    )
                )

        except Exception as e:
            logger.warning(f"Error searching HN for '{query}': {e}")

        return posts

    def test(self) -> str:
        """Test Algolia API connection."""
        import asyncio

        async def _test():
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{ALGOLIA_API_URL}/search", params={"query": "test"}
                )
                response.raise_for_status()
                return f"{self.name} scraper: Connected successfully"

        try:
            return asyncio.run(_test())
        except Exception as e:
            return f"{self.name} scraper: Connection failed - {e}"
