"""Product Hunt scraper."""

import asyncio
import logging
import httpx
from datetime import datetime, timezone
from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper, ScrapedPost
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

PRODUCT_HUNT_URL = "https://www.producthunt.com"


class ProductHuntScraper(BaseScraper):
    """Scraper for Product Hunt using web scraping."""

    name = "product_hunt"

    async def scrape(self) -> list[ScrapedPost]:
        """Scrape today's top products from Product Hunt."""
        posts = []

        async with httpx.AsyncClient() as client:
            try:
                # Get the main page
                response = await client.get(
                    PRODUCT_HUNT_URL,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                    },
                    follow_redirects=True,
                )
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "lxml")

                # Find product cards (structure may change)
                # Product Hunt uses React, so we need to look for data attributes
                product_sections = soup.find_all("div", {"data-test": "post-item"})

                if not product_sections:
                    # Fallback: try to find any section with product-like structure
                    product_sections = soup.find_all("section")[:20]

                for section in product_sections[:20]:
                    try:
                        # Try to extract product info
                        title_elem = (
                            section.find("h3")
                            or section.find("h2")
                            or section.find("a")
                        )
                        desc_elem = section.find("p")

                        if title_elem:
                            title = title_elem.get_text(strip=True)
                            description = (
                                desc_elem.get_text(strip=True) if desc_elem else ""
                            )

                            # Get link
                            link_elem = section.find("a", href=True)
                            url = link_elem["href"] if link_elem else ""
                            if url and not url.startswith("http"):
                                url = f"{PRODUCT_HUNT_URL}{url}"

                            content = f"{title}\n\n{description}"

                            if len(content) > 20:  # Filter out empty/short content
                                posts.append(
                                    ScrapedPost(
                                        source=self.name,
                                        external_id=f"ph_{hash(title)}_{datetime.now(timezone.utc).strftime('%Y%m%d')}",
                                        content=content,
                                        author=None,
                                        url=url or PRODUCT_HUNT_URL,
                                        engagement=0,
                                        created_at=datetime.now(timezone.utc),
                                    )
                                )

                    except Exception as e:
                        logger.warning(f"Error parsing product section: {e}")
                        continue

            except Exception as e:
                logger.warning(f"Error scraping Product Hunt: {e}")

        return posts

    def test(self) -> str:
        """Test Product Hunt connection."""

        async def _test():
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    PRODUCT_HUNT_URL,
                    headers={"User-Agent": "Mozilla/5.0"},
                    follow_redirects=True,
                )
                response.raise_for_status()
                return f"{self.name} scraper: Connected successfully"

        try:
            return asyncio.run(_test())
        except Exception as e:
            return f"{self.name} scraper: Connection failed - {e}"
