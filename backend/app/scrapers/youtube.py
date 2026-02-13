"""YouTube scraper using YouTube Data API v3."""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from app.config import get_settings
from app.scrapers.base import BaseScraper, ScrapedPost

logger = logging.getLogger(__name__)
settings = get_settings()

# YouTube API configuration
YOUTUBE_API_BASE_URL = "https://www.googleapis.com/youtube/v3"
YOUTUBE_API_KEY = getattr(settings, "youtube_api_key", "")

# Categories for trending videos
TRENDING_CATEGORIES = {
    "tech": "Technology & Software",
    "education": "Education",
    "howto": "Howto & Style",
}

# Opportunity signal keywords for YouTube content
OPPORTUNITY_KEYWORDS = [
    # Direct tool/app requests
    "best app for",
    "looking for app",
    "need a tool",
    "recommendation for",
    "what software",
    "any apps",
    "is there an app",
    # Problem statements
    "struggling with",
    "frustrated by",
    "tired of",
    "can't find",
    "need help with",
    "how do you",
    "what do you use",
    # Solution seeking
    "alternatives to",
    "better than",
    "replacement for",
    "switching from",
    "moving away from",
    # Build/create interest
    "thinking of building",
    "want to create",
    "planning to develop",
    "would anyone use",
    "is there a market",
    # Tutorial requests
    "how to automate",
    "how to streamline",
    "need tutorial",
    "step by step",
    "guide me",
    # Pain points
    "too complicated",
    "too expensive",
    "doesn't work",
    "broken workflow",
    "waste of time",
    # Budget/pricing
    "willing to pay",
    "ready to pay",
    "budget friendly",
    "free alternative",
    "cost effective",
    # Turkish keywords
    "en iyi uygulama",
    "arıyorum",
    "ihtiyacım var",
    "öneri",
    "alternatif",
    "yardım",
    "nasıl yapılır",
]

# App/software mention patterns
APP_PATTERNS = [
    # Common app indicators
    "app",
    "software",
    "tool",
    "platform",
    "service",
    "application",
    "program",
    "system",
    "solution",
    # Tech stack terms
    "api",
    "saas",
    "web app",
    "mobile app",
    "desktop",
    "extension",
    "plugin",
    "addon",
    "integration",
    # Action words
    "download",
    "install",
    "use",
    "try",
    "test",
    "review",
]

# Search queries for app reviews
APP_REVIEW_QUERIES = [
    "app review",
    "software review",
    "best apps for",
    "top tools for",
    "tutorial",
    "how to use",
    "vs comparison",
    "alternative to",
    "setup guide",
    "demo",
]


class YouTubeScraper(BaseScraper):
    """Scraper for YouTube using YouTube Data API v3."""

    name = "youtube"

    # API limits and quotas
    MAX_RESULTS_PER_REQUEST = 50
    DAILY_QUOTA_LIMIT = 10000
    COST_PER_SEARCH = 100
    COST_PER_VIDEO_DETAILS = 1
    COST_PER_COMMENTS = 1

    # Engagement thresholds
    MIN_VIEWS_FOR_COMMENTS = 1000
    MAX_COMMENTS_PER_VIDEO = 20

    def __init__(self):
        self._rate_limit_delay = max(1.0, settings.request_delay_seconds)
        self._api_key = YOUTUBE_API_KEY
        if not self._api_key:
            logger.warning(
                "YouTube API key not configured. Set YOUTUBE_API_KEY in environment."
            )

    async def scrape(self) -> list[ScrapedPost]:
        """Main scrape method - combines all YouTube sources."""
        if not self._api_key:
            logger.error("YouTube API key not configured")
            return []

        all_posts = []

        # Scrape trending videos
        try:
            trending_posts = await self.scrape_trending()
            all_posts.extend(trending_posts)
            logger.info(f"Scraped {len(trending_posts)} trending videos")
        except Exception as e:
            logger.error(f"Error scraping trending videos: {e}")

        # Scrape app review videos
        try:
            app_review_posts = await self.scrape_app_reviews()
            all_posts.extend(app_review_posts)
            logger.info(f"Scraped {len(app_review_posts)} app review videos")
        except Exception as e:
            logger.error(f"Error scraping app reviews: {e}")

        # Detect app mentions
        try:
            app_mention_posts = await self.detect_app_mentions()
            all_posts.extend(app_mention_posts)
            logger.info(f"Scraped {len(app_mention_posts)} app mention videos")
        except Exception as e:
            logger.error(f"Error detecting app mentions: {e}")

        # Scrape educational content
        try:
            educational_posts = await self.scrape_educational_content()
            all_posts.extend(educational_posts)
            logger.info(f"Scraped {len(educational_posts)} educational videos")
        except Exception as e:
            logger.error(f"Error scraping educational content: {e}")

        logger.info(f"YouTube scrape complete: {len(all_posts)} total posts")
        return all_posts

    async def scrape_trending(self, category: str = "tech") -> list[ScrapedPost]:
        """Scrape YouTube trending videos."""
        if not self._api_key:
            return []

        posts = []

        # Get category ID (default to Tech category)
        category_id = "28"  # Technology category ID
        if category == "education":
            category_id = "27"  # Education category ID
        elif category == "howto":
            category_id = "26"  # Howto & Style category ID

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Get trending videos
                url = f"{YOUTUBE_API_BASE_URL}/videos"
                params = {
                    "part": "snippet,statistics",
                    "chart": "mostPopular",
                    "regionCode": "US",
                    "categoryId": category_id,
                    "maxResults": self.MAX_RESULTS_PER_REQUEST,
                    "key": self._api_key,
                }

                response = await self._make_api_request(client, url, params)
                if not response:
                    return []

                data = response.json()
                videos = data.get("items", [])

                # Process each video
                for video in videos:
                    post = await self._process_video_data(video, "trending")
                    if post:
                        posts.append(post)

                # Get comments for high-engagement videos
                for post in posts:
                    if post.engagement >= self.MIN_VIEWS_FOR_COMMENTS:
                        comments = await self._fetch_video_comments(
                            post.external_id, client
                        )
                        posts.extend(comments)

        except Exception as e:
            logger.error(f"Error scraping trending videos: {e}")

        return posts

    async def scrape_app_reviews(self, app_name: str = "") -> list[ScrapedPost]:
        """Search for app review videos."""
        if not self._api_key:
            return []

        posts = []

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Search for app review videos
                for query in APP_REVIEW_QUERIES:
                    if app_name:
                        search_query = f"{app_name} {query}"
                    else:
                        search_query = query

                    url = f"{YOUTUBE_API_BASE_URL}/search"
                    params = {
                        "part": "snippet",
                        "q": search_query,
                        "type": "video",
                        "maxResults": min(25, self.MAX_RESULTS_PER_REQUEST // 2),
                        "relevanceLanguage": "en",
                        "key": self._api_key,
                    }

                    response = await self._make_api_request(client, url, params)
                    if not response:
                        continue

                    data = response.json()
                    videos = data.get("items", [])

                    # Get detailed video information
                    video_ids = [video["id"]["videoId"] for video in videos]
                    detailed_videos = await self._get_video_details(video_ids, client)

                    for video in detailed_videos:
                        post = await self._process_video_data(video, "app_review")
                        if post and self._has_opportunity_signal(post.content):
                            posts.append(post)

                    # Rate limiting between searches
                    await asyncio.sleep(self._rate_limit_delay)

        except Exception as e:
            logger.error(f"Error scraping app reviews: {e}")

        return posts

    async def detect_app_mentions(self) -> list[ScrapedPost]:
        """Detect apps mentioned in YouTube content."""
        if not self._api_key:
            return []

        posts = []

        # Search for videos mentioning apps/software
        search_queries = [
            "best software 2024",
            "must have apps",
            "productivity tools",
            "business software",
            "tech stack",
            "software recommendations",
            "favorite apps",
            "essential tools",
        ]

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                for query in search_queries:
                    url = f"{YOUTUBE_API_BASE_URL}/search"
                    params = {
                        "part": "snippet",
                        "q": query,
                        "type": "video",
                        "maxResults": min(20, self.MAX_RESULTS_PER_REQUEST // 4),
                        "relevanceLanguage": "en",
                        "key": self._api_key,
                    }

                    response = await self._make_api_request(client, url, params)
                    if not response:
                        continue

                    data = response.json()
                    videos = data.get("items", [])

                    # Get detailed video information
                    video_ids = [video["id"]["videoId"] for video in videos]
                    detailed_videos = await self._get_video_details(video_ids, client)

                    for video in detailed_videos:
                        post = await self._process_video_data(video, "app_mention")
                        if post and self._contains_app_mentions(post.content):
                            posts.append(post)

                    await asyncio.sleep(self._rate_limit_delay)

        except Exception as e:
            logger.error(f"Error detecting app mentions: {e}")

        return posts

    async def scrape_educational_content(self) -> list[ScrapedPost]:
        """Scrape educational videos for tool requests."""
        if not self._api_key:
            return []

        posts = []

        # Search for educational/how-to content
        educational_queries = [
            "how to automate",
            "tutorial for beginners",
            "step by step guide",
            "workflow automation",
            "productivity tutorial",
            "business process",
            "tool tutorial",
            "software guide",
        ]

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                for query in educational_queries:
                    url = f"{YOUTUBE_API_BASE_URL}/search"
                    params = {
                        "part": "snippet",
                        "q": query,
                        "type": "video",
                        "maxResults": min(20, self.MAX_RESULTS_PER_REQUEST // 4),
                        "relevanceLanguage": "en",
                        "key": self._api_key,
                    }

                    response = await self._make_api_request(client, url, params)
                    if not response:
                        continue

                    data = response.json()
                    videos = data.get("items", [])

                    # Get detailed video information
                    video_ids = [video["id"]["videoId"] for video in videos]
                    detailed_videos = await self._get_video_details(video_ids, client)

                    for video in detailed_videos:
                        post = await self._process_video_data(video, "educational")
                        if post and self._has_opportunity_signal(post.content):
                            posts.append(post)

                            # Get comments for educational content (high value)
                            if post.engagement >= self.MIN_VIEWS_FOR_COMMENTS // 2:
                                comments = await self._fetch_video_comments(
                                    post.external_id, client
                                )
                                posts.extend(comments)

                    await asyncio.sleep(self._rate_limit_delay)

        except Exception as e:
            logger.error(f"Error scraping educational content: {e}")

        return posts

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
        before_sleep=lambda retry_state: logger.warning(
            f"YouTube API retry attempt {retry_state.attempt_number}"
        ),
    )
    async def _make_api_request(
        self, client: httpx.AsyncClient, url: str, params: dict
    ) -> httpx.Response | None:
        """Make API request with error handling."""
        try:
            response = await client.get(url, params=params)

            if response.status_code == 403:
                logger.error("YouTube API quota exceeded or invalid API key")
                return None
            elif response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                logger.warning(f"YouTube API rate limited, waiting {retry_after}s")
                await asyncio.sleep(retry_after)
                response = await client.get(url, params=params)

            response.raise_for_status()
            return response

        except Exception as e:
            logger.error(f"YouTube API request failed: {e}")
            return None

    async def _get_video_details(
        self, video_ids: list[str], client: httpx.AsyncClient
    ) -> list[dict]:
        """Get detailed video information."""
        if not video_ids:
            return []

        url = f"{YOUTUBE_API_BASE_URL}/videos"
        params = {
            "part": "snippet,statistics",
            "id": ",".join(video_ids),
            "key": self._api_key,
        }

        response = await self._make_api_request(client, url, params)
        if not response:
            return []

        data = response.json()
        return data.get("items", [])

    async def _fetch_video_comments(
        self, video_id: str, client: httpx.AsyncClient
    ) -> list[ScrapedPost]:
        """Fetch comments from a video."""
        comments = []

        try:
            url = f"{YOUTUBE_API_BASE_URL}/commentThreads"
            params = {
                "part": "snippet",
                "videoId": video_id,
                "maxResults": self.MAX_COMMENTS_PER_VIDEO,
                "order": "relevance",
                "key": self._api_key,
            }

            response = await self._make_api_request(client, url, params)
            if not response:
                return []

            data = response.json()
            comment_threads = data.get("items", [])

            for thread in comment_threads:
                comment = thread.get("snippet", {}).get("topLevelComment", {})
                comment_data = comment.get("snippet", {})

                content = comment_data.get("text", "")
                author = comment_data.get("authorDisplayName", "")
                likes = comment_data.get("likeCount", 0)

                # Only include comments with opportunity signals
                if content and self._has_opportunity_signal(content):
                    comments.append(
                        ScrapedPost(
                            source=f"{self.name}_comment",
                            external_id=f"comment_{comment.get('id', '')}",
                            content=content,
                            author=author,
                            url=f"https://youtube.com/watch?v={video_id}",
                            engagement=likes,
                            created_at=datetime.fromisoformat(
                                comment_data.get(
                                    "updatedAt", comment_data.get("publishedAt", "")
                                ).replace("Z", "+00:00")
                            )
                            if comment_data.get("publishedAt")
                            else None,
                        )
                    )

        except Exception as e:
            logger.debug(f"Error fetching comments for video {video_id}: {e}")

        return comments

    async def _process_video_data(
        self, video: dict, source_type: str
    ) -> ScrapedPost | None:
        """Process video data into ScrapedPost."""
        try:
            snippet = video.get("snippet", {})
            statistics = video.get("statistics", {})

            video_id = video.get("id", "")
            title = snippet.get("title", "")
            description = snippet.get("description", "")
            channel = snippet.get("channelTitle", "")

            # Combine title and description for content
            content = f"{title}\n\n{description}"

            # Calculate engagement (views + likes + comments)
            views = int(statistics.get("viewCount", 0))
            likes = int(statistics.get("likeCount", 0))
            comments = int(statistics.get("commentCount", 0))
            engagement = views + likes + comments

            # Parse publish date
            published_at = snippet.get("publishedAt", "")
            created_at = None
            if published_at:
                created_at = datetime.fromisoformat(published_at.replace("Z", "+00:00"))

            return ScrapedPost(
                source=f"{self.name}_{source_type}",
                external_id=video_id,
                content=content,
                author=channel,
                url=f"https://youtube.com/watch?v={video_id}",
                engagement=engagement,
                created_at=created_at,
            )

        except Exception as e:
            logger.error(f"Error processing video data: {e}")
            return None

    def _has_opportunity_signal(self, content: str) -> bool:
        """Check if content contains opportunity-related keywords."""
        content_lower = content.lower()
        return any(keyword.lower() in content_lower for keyword in OPPORTUNITY_KEYWORDS)

    def _contains_app_mentions(self, content: str) -> bool:
        """Check if content mentions apps/software."""
        content_lower = content.lower()
        return any(pattern.lower() in content_lower for pattern in APP_PATTERNS)

    def test(self) -> str:
        """Test YouTube API connection."""
        if not self._api_key:
            return f"{self.name} scraper: API key not configured"

        async def _test():
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    url = f"{YOUTUBE_API_BASE_URL}/videos"
                    params = {
                        "part": "snippet",
                        "chart": "mostPopular",
                        "regionCode": "US",
                        "maxResults": 1,
                        "key": self._api_key,
                    }

                    response = await self._make_api_request(client, url, params)
                    if not response:
                        return f"{self.name} scraper: API request failed"

                    data = response.json()
                    if "items" in data and data["items"]:
                        logger.info("YouTube API connection test successful")
                        return f"{self.name} scraper: Connected successfully"
                    else:
                        return f"{self.name} scraper: Unexpected response format"

            except Exception as e:
                logger.error(f"YouTube connection failed: {e}")
                return f"{self.name} scraper: Connection failed - {e}"

        # Run async test
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, _test())
                return future.result()
        else:
            return loop.run_until_complete(_test())
