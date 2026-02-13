"""GitHub trending scraper for open source project trends."""

import logging
from datetime import datetime, timezone
from typing import List
import httpx
from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper, ScrapedPost

logger = logging.getLogger(__name__)


class GitHubTrendingScraper(BaseScraper):
    """Scrape GitHub trending repositories to identify technology trends."""

    name = "github_trending"

    def __init__(self):
        self.base_url = "https://github.com/trending"
        self.time_ranges = ["daily", "weekly"]
        self.languages = ["python", "typescript", "javascript", "go", "rust", ""]

    async def scrape(self) -> List[ScrapedPost]:
        """Scrape GitHub trending repositories."""
        posts = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            for time_range in self.time_ranges:
                for language in self.languages:
                    try:
                        trending = await self._scrape_trending(
                            client, time_range, language
                        )
                        posts.extend(trending)
                    except Exception as e:
                        logger.error(
                            f"Error scraping GitHub trending {time_range}/{language}: {e}"
                        )
                        continue

        logger.info(f"GitHub Trending scraper found {len(posts)} repositories")
        return posts

    async def _scrape_trending(
        self, client: httpx.AsyncClient, time_range: str, language: str
    ) -> List[ScrapedPost]:
        """Scrape trending repositories for a specific time range and language."""
        posts = []

        url = self.base_url
        params = {}

        if time_range == "weekly":
            params["since"] = "weekly"

        if language:
            url = f"{self.base_url}/{language}"
            if time_range == "weekly":
                params["since"] = "weekly"

        try:
            response = await client.get(
                url,
                params=params,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "text/html",
                },
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Find trending repository articles
            repo_articles = soup.find_all("article", class_="Box-row")

            for idx, article in enumerate(repo_articles[:15]):  # Top 15 per category
                try:
                    # Extract repository info
                    h2_elem = article.find("h2")
                    if not h2_elem:
                        continue

                    # Get repo name and URL
                    link_elem = h2_elem.find("a")
                    if not link_elem:
                        continue

                    repo_path = link_elem.get("href", "").strip("/")
                    if not repo_path:
                        continue

                    # Get description
                    description_elem = article.find("p", class_="col-9")
                    description = (
                        description_elem.text.strip() if description_elem else ""
                    )

                    # Get star count
                    star_elem = article.find(
                        "a",
                        class_="Link--muted",
                        href=lambda x: x and "stargazers" in x,
                    )
                    stars = 0
                    if star_elem:
                        star_text = star_elem.text.strip().replace(",", "")
                        try:
                            stars = int(star_text)
                        except ValueError:
                            pass

                    # Get language
                    lang_elem = article.find("span", itemprop="programmingLanguage")
                    language_name = lang_elem.text.strip() if lang_elem else "Unknown"

                    # Build content
                    content = (
                        f"GitHub Trending: {repo_path} ({language_name}). {description}"
                    )
                    if stars > 0:
                        content += f" ⭐ {stars:,} stars"

                    post = ScrapedPost(
                        source=self.name,
                        external_id=f"github_{repo_path.replace('/', '_')}_{time_range}",
                        content=content[:500],
                        author=repo_path.split("/")[0] if "/" in repo_path else None,
                        url=f"https://github.com/{repo_path}",
                        engagement=stars,
                        created_at=datetime.now(timezone.utc),
                    )
                    posts.append(post)

                except Exception as e:
                    logger.warning(f"Error parsing repository: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error fetching GitHub trending: {e}")

        return posts
