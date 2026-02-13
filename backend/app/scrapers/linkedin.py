"""LinkedIn scraper for job postings and professional trends."""

import logging
from datetime import datetime, timezone
from typing import List
import httpx
from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper, ScrapedPost

logger = logging.getLogger(__name__)


class LinkedInScraper(BaseScraper):
    """Scrape LinkedIn job postings to identify skill demands and market trends."""

    name = "linkedin"

    def __init__(self):
        self.base_url = "https://www.linkedin.com/jobs/search"
        self.keywords = [
            "AI startups",
            "machine learning",
            "SaaS product manager",
            "fintech",
            "healthtech",
            "climate tech",
            "remote startup",
        ]

    async def scrape(self) -> List[ScrapedPost]:
        """Scrape LinkedIn job postings for trending skills and opportunities."""
        posts = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            for keyword in self.keywords:
                try:
                    search_posts = await self._search_jobs(client, keyword)
                    posts.extend(search_posts)
                except Exception as e:
                    logger.error(
                        f"Error scraping LinkedIn for keyword '{keyword}': {e}"
                    )
                    continue

        logger.info(f"LinkedIn scraper found {len(posts)} job postings")
        return posts

    async def _search_jobs(
        self, client: httpx.AsyncClient, keyword: str
    ) -> List[ScrapedPost]:
        """Search for jobs by keyword and extract relevant postings."""
        posts = []

        params = {
            "keywords": keyword,
            "location": "United States",
            "f_TPR": "r86400",  # Last 24 hours
        }

        try:
            response = await client.get(
                self.base_url,
                params=params,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            job_cards = soup.find_all("div", class_="base-card")

            for idx, card in enumerate(job_cards[:20]):  # Limit to 20 per keyword
                try:
                    title_elem = card.find("h3", class_="base-search-card__title")
                    company_elem = card.find("h4", class_="base-search-card__subtitle")
                    link_elem = card.find("a", class_="base-card__full-link")

                    if not all([title_elem, company_elem]):
                        continue

                    title = title_elem.text.strip()
                    company = company_elem.text.strip()
                    job_url = link_elem.get("href", "") if link_elem else ""

                    # Create content from job posting
                    content = (
                        f"Job posting: {title} at {company}. Looking for: {keyword}."
                    )

                    post = ScrapedPost(
                        source=self.name,
                        external_id=f"linkedin_{keyword.replace(' ', '_')}_{idx}_{datetime.now(timezone.utc).strftime('%Y%m%d')}",
                        content=content,
                        author=company,
                        url=job_url,
                        engagement=0,
                        created_at=datetime.now(timezone.utc),
                    )
                    posts.append(post)

                except Exception as e:
                    logger.warning(f"Error parsing job card: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error fetching LinkedIn jobs for '{keyword}': {e}")

        return posts
