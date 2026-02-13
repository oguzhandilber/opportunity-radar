"""Base scraper interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone

from app.database import RawPost, get_db_context


@dataclass
class ScrapedPost:
    """Represents a scraped post from any source."""

    source: str
    external_id: str
    content: str
    author: str | None = None
    url: str | None = None
    engagement: int = 0
    created_at: datetime | None = None


class BaseScraper(ABC):
    """Base class for all scrapers."""

    name: str = "base"

    @abstractmethod
    async def scrape(self) -> list[ScrapedPost]:
        """Scrape posts from the source. Must be implemented by subclasses."""
        pass

    async def save_posts(self, posts: list[ScrapedPost]) -> int:
        """Save scraped posts to database, skipping duplicates."""
        saved_count = 0

        async with get_db_context() as session:
            for post in posts:
                # Check if already exists
                from sqlalchemy import select

                query = select(RawPost).where(
                    RawPost.source == post.source,
                    RawPost.external_id == post.external_id,
                )
                result = await session.execute(query)
                existing = result.scalar_one_or_none()

                if not existing:
                    raw_post = RawPost(
                        source=post.source,
                        external_id=post.external_id,
                        content=post.content,
                        author=post.author,
                        url=post.url,
                        engagement=post.engagement,
                        created_at=post.created_at or datetime.now(timezone.utc),
                        scraped_at=datetime.now(timezone.utc),
                    )
                    session.add(raw_post)
                    saved_count += 1

            await session.commit()

        return saved_count

    def test(self) -> str:
        """Test the scraper connection."""
        return f"{self.name} scraper is ready"
