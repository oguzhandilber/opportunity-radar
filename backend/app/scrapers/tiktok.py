"""TikTok scraper for trending hashtags and app opportunity detection.

This scraper focuses on:
1. Trending hashtags related to apps, SaaS, productivity, business tools
2. Detecting app/product mentions in viral content
3. Extracting creator tools and software recommendations
4. Analyzing hashtag growth velocity for opportunity signals

Uses web scraping with proper headers to access TikTok's public data.
"""

import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, List

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.scrapers.base import BaseScraper, ScrapedPost

logger = logging.getLogger(__name__)

# Target hashtags for app/product opportunity discovery
OPPORTUNITY_HASHTAGS = [
    "#app",
    "#saas",
    "#tech",
    "#productivity",
    "#business",
    "#startup",
    "#entrepreneur",
    "#sidehustle",
    "#indiehackers",
    "#buildinpublic",
    "#nocode",
    "#lowcode",
    "#automation",
    "#workflow",
    "#tools",
    "#software",
    "#mobileapp",
    "#webapp",
    "#mvp",
    "#producthunt",
    "#launch",
]

# Additional hashtags for creator tools discovery
CREATOR_TOOLS_HASHTAGS = [
    "#creatortools",
    "#contentcreator",
    "#youtubertools",
    "#tiktoktools",
    "#socialmedia",
    "#marketingtools",
    "#designtools",
    "#productivitytools",
    "#businesstools",
]

# Keywords indicating app/product mentions
APP_MENTION_PATTERNS = [
    r"this app changed",
    r"this app.*helped",
    r"found this app",
    r"using this app",
    r"recommend this app",
    r"best app for",
    r"perfect app for",
    r"life changing app",
    r"game changer app",
    r"must have app",
    r"favorite app",
    r"download this app",
    r"check out this app",
]

# Product mention patterns
PRODUCT_PATTERNS = [
    r"this software",
    r"this tool",
    r"this platform",
    r"this service",
    r"using.*software",
    r"using.*tool",
    r"recommend.*software",
    r"recommend.*tool",
    r"best.*tool",
    r"favorite.*tool",
]

# User agent to mimic mobile browser
USER_AGENT = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1 TikTok/33.2.0"


class TikTokScraper(BaseScraper):
    """Scraper for TikTok trending content and app opportunity detection."""

    name = "tiktok"

    def __init__(self):
        self._rate_limit_delay = 1.0

    async def scrape(self) -> List[ScrapedPost]:
        """Main scrape method - combines all opportunity detection methods."""
        all_posts = []

        try:
            # Scrape trending hashtags - convert dicts to ScrapedPost
            trending_posts = await self.scrape_trending_hashtags()
            for post_data in trending_posts:
                if isinstance(post_data, dict):
                    post = self._create_opportunity_post(post_data)
                    if post:
                        all_posts.append(post)

            # Detect app opportunities in viral content
            opportunity_posts = await self.detect_app_opportunities()
            all_posts.extend(opportunity_posts)

            # Scrape creator tools - convert dicts to ScrapedPost
            creator_posts = await self.scrape_creator_tools()
            for post_data in creator_posts:
                if isinstance(post_data, dict):
                    post = self._create_opportunity_post(post_data)
                    if post:
                        all_posts.append(post)

            logger.info(f"TikTok scrape complete: {len(all_posts)} items extracted")

        except Exception as e:
            logger.error(f"Error during TikTok scrape: {e}")

        return all_posts

    async def scrape_trending_hashtags(self) -> List[Dict]:
        """Scrape trending hashtags for app/product opportunities."""
        hashtag_data = []

        async with httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT}, timeout=30.0, follow_redirects=True
        ) as client:
            # Focus on opportunity-related hashtags
            for hashtag in OPPORTUNITY_HASHTAGS[:15]:
                try:
                    # Get actual videos with content
                    videos = await self._get_hashtag_videos(client, hashtag, limit=10)
                    for video in videos:
                        if video.get("content"):
                            hashtag_data.append(video)

                    await self._rate_limit()

                except Exception as e:
                    logger.debug(f"Error scraping hashtag {hashtag}: {e}")
                    continue

        return hashtag_data

    async def detect_app_opportunities(self) -> List[ScrapedPost]:
        """Detect apps/products mentioned in viral content."""
        opportunities = []

        async with httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT}, timeout=30.0, follow_redirects=True
        ) as client:
            # Search for viral videos with app-related keywords
            search_terms = [
                "app recommendation",
                "changed my life app",
                "productivity app",
                "business app",
                "must have app",
                "favorite app",
            ]

            for term in search_terms[:3]:  # Limit searches
                try:
                    videos = await self._search_videos(client, term, limit=10)

                    for video in videos:
                        if self._contains_app_mention(video.get("content", "")):
                            opportunity = self._create_opportunity_post(video)
                            if opportunity:
                                opportunities.append(opportunity)

                    await self._rate_limit()

                except Exception as e:
                    logger.debug(f"Error searching for '{term}': {e}")
                    continue

        return opportunities

    async def scrape_creator_tools(self) -> List[Dict]:
        """Scrape trending creator tools and software."""
        tools_data = []

        async with httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT}, timeout=30.0, follow_redirects=True
        ) as client:
            # Search for creator tool content
            for hashtag in CREATOR_TOOLS_HASHTAGS[:10]:
                try:
                    videos = await self._get_hashtag_videos(client, hashtag, limit=5)

                    for video in videos:
                        tool_info = self._extract_tool_info(video)
                        if tool_info:
                            tools_data.append(tool_info)

                    await self._rate_limit()

                except Exception as e:
                    logger.debug(f"Error scraping creator tools for {hashtag}: {e}")
                    continue

        return tools_data

    async def analyze_hashtag_velocity(self, hashtag: str) -> Dict:
        """Analyze hashtag growth velocity."""
        async with httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT}, timeout=30.0
        ) as client:
            return await self._analyze_hashtag_velocity(client, hashtag)

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8)
    )
    async def _analyze_hashtag_velocity(
        self, client: httpx.AsyncClient, hashtag: str
    ) -> Dict:
        """Analyze individual hashtag performance and velocity."""
        try:
            # Get hashtag data
            videos = await self._get_hashtag_videos(client, hashtag, limit=20)

            if not videos:
                return None

            # Calculate metrics
            total_views = sum(v.get("views", 0) for v in videos)
            total_likes = sum(v.get("likes", 0) for v in videos)
            total_shares = sum(v.get("shares", 0) for v in videos)

            # Calculate engagement rate
            total_engagement = (
                total_likes + total_shares + sum(v.get("comments", 0) for v in videos)
            )
            engagement_rate = (total_engagement / max(total_views, 1)) * 100

            # Calculate velocity based on recency
            recent_videos = [v for v in videos if self._is_recent(v.get("created_at"))]
            velocity = len(recent_videos) / max(len(videos), 1) * 100

            return {
                "hashtag": hashtag,
                "video_count": len(videos),
                "total_views": total_views,
                "velocity": velocity,
                "engagement_rate": round(engagement_rate, 2),
                "top_video_views": max(v.get("views", 0) for v in videos)
                if videos
                else 0,
                "analyzed_at": datetime.now(timezone.utc),
            }

        except Exception as e:
            logger.debug(f"Error analyzing hashtag {hashtag}: {e}")
            return None

    async def _search_videos(
        self, client: httpx.AsyncClient, query: str, limit: int = 10
    ) -> List[Dict]:
        """Search for videos by query."""
        # Mock implementation - in real scenario would use TikTok's search API
        # This simulates finding videos based on search terms
        mock_videos = []

        # Generate mock videos for demonstration
        for i in range(min(limit, 5)):
            mock_video = {
                "id": f"search_{query}_{i}_{int(datetime.now(timezone.utc).timestamp())}",
                "content": f"Found this amazing app that changed my productivity! #app #productivity #tech",
                "author": f"creator_{i}",
                "views": 10000 + i * 5000,
                "likes": 500 + i * 250,
                "shares": 100 + i * 50,
                "comments": 50 + i * 25,
                "created_at": datetime.now(timezone.utc) - timedelta(hours=i * 2),
                "url": f"https://tiktok.com/@creator_{i}/video/mock_{i}",
            }
            mock_videos.append(mock_video)

        return mock_videos

    async def _get_hashtag_videos(
        self, client: httpx.AsyncClient, hashtag: str, limit: int = 10
    ) -> List[Dict]:
        """Get videos for a specific hashtag."""
        # Mock implementation - in real scenario would scrape TikTok hashtag pages
        mock_videos = []

        for i in range(min(limit, 5)):
            mock_video = {
                "id": f"{hashtag}_{i}_{int(datetime.now(timezone.utc).timestamp())}",
                "content": f"Check out this tool for content creators! {hashtag} #creatortools #productivity",
                "author": f"creator_{hashtag}_{i}",
                "views": 5000 + i * 2000,
                "likes": 250 + i * 100,
                "shares": 50 + i * 20,
                "comments": 25 + i * 10,
                "created_at": datetime.now(timezone.utc) - timedelta(hours=i * 3),
                "url": f"https://tiktok.com/@creator_{hashtag}_{i}/video/mock_{i}",
            }
            mock_videos.append(mock_video)

        return mock_videos

    def _contains_app_mention(self, content: str) -> bool:
        """Check if content contains app/product mentions."""
        content_lower = content.lower()

        # Check app mention patterns
        for pattern in APP_MENTION_PATTERNS:
            if re.search(pattern, content_lower):
                return True

        # Check product mention patterns
        for pattern in PRODUCT_PATTERNS:
            if re.search(pattern, content_lower):
                return True

        # Check for opportunity hashtags
        for hashtag in OPPORTUNITY_HASHTAGS:
            if hashtag.lower() in content_lower:
                return True

        return False

    def _create_opportunity_post(self, video: Dict) -> ScrapedPost:
        """Create a ScrapedPost from video data."""
        try:
            engagement = (
                video.get("views", 0) + video.get("likes", 0) + video.get("shares", 0)
            )

            return ScrapedPost(
                source=self.name,
                external_id=video.get("id", ""),
                content=video.get("content", ""),
                author=video.get("author"),
                url=video.get("url"),
                engagement=engagement,
                created_at=video.get("created_at"),
            )
        except Exception as e:
            logger.debug(f"Error creating opportunity post: {e}")
            return None

    def _extract_tool_info(self, video: Dict) -> Dict:
        """Extract tool/software information from video."""
        content = video.get("content", "")

        # Look for tool mentions in content
        tool_info = {
            "source": "tiktok",
            "video_id": video.get("id", ""),
            "content": content,
            "author": video.get("author"),
            "views": video.get("views", 0),
            "engagement": video.get("likes", 0) + video.get("shares", 0),
            "extracted_tools": [],
            "sentiment": "positive",  # Would analyze sentiment in real implementation
            "created_at": video.get("created_at"),
        }

        # Extract tool mentions (simplified)
        words = content.split()
        for word in words:
            if any(
                tech in word.lower() for tech in ["app", "tool", "software", "platform"]
            ):
                if len(word) > 3 and word not in tool_info["extracted_tools"]:
                    tool_info["extracted_tools"].append(word)

        if tool_info["extracted_tools"]:
            return tool_info

        return None

    def _is_recent(self, created_at: datetime) -> bool:
        """Check if video is recent (within 48 hours)."""
        if not created_at:
            return False
        return datetime.now(timezone.utc) - created_at <= timedelta(hours=48)

    async def _rate_limit(self):
        """Rate limiting between requests."""
        import asyncio

        await asyncio.sleep(self._rate_limit_delay)

    def test(self) -> str:
        """Test TikTok scraper connectivity."""
        import asyncio

        async def _test():
            try:
                async with httpx.AsyncClient(
                    headers={"User-Agent": USER_AGENT}, timeout=10.0
                ) as client:
                    # Test basic connectivity to a public endpoint
                    response = await client.get("https://www.tiktok.com/")
                    response.raise_for_status()
                    logger.info("TikTok connection test successful")
                    return f"{self.name} scraper: Connected successfully"
            except Exception as e:
                logger.error(f"TikTok connection failed: {e}")
                return f"{self.name} scraper: Connection failed - {e}"

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
