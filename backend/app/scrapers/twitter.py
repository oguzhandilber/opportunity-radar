"""Twitter/X scraper for opportunity discovery.

This scraper implements Twitter API v2 integration for comprehensive data collection
including trending topics, opportunity search, viral content detection, and hashtag monitoring.
"""

import logging
import httpx
import re
import os
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from dataclasses import dataclass

from app.scrapers.base import BaseScraper, ScrapedPost

logger = logging.getLogger(__name__)


@dataclass
class TwitterConfig:
    """Configuration for Twitter API access."""

    bearer_token: Optional[str] = None
    api_base_url: str = "https://api.twitter.com/2"
    rate_limit_window: int = 900  # 15 minutes
    max_requests_per_window: int = 300


class TwitterScraper(BaseScraper):
    """Twitter/X scraper for opportunity discovery using API v2."""

    name = "twitter"

    def __init__(self):
        self.config = TwitterConfig(bearer_token=os.getenv("TWITTER_BEARER_TOKEN"))
        self._last_request_time = 0
        self._request_count = 0

    async def scrape(self) -> List[ScrapedPost]:
        """Main scrape method - combines trending and opportunity search."""
        all_posts = []

        try:
            # Get trending topics
            trending_posts = await self.scrape_trending()
            all_posts.extend(trending_posts)

            # Search for specific opportunity signals
            opportunity_posts = await self.search_opportunities(
                "startup OR SaaS OR productivity"
            )
            all_posts.extend(opportunity_posts[:10])  # Limit to top 10

        except Exception as e:
            logger.error(f"Error in main scrape: {e}")

        return all_posts

    async def scrape_trending(self) -> List[ScrapedPost]:
        """Scrape Twitter trending topics for tech/business opportunities."""
        posts = []

        # Focus hashtags for tech/business opportunities
        tech_hashtags = [
            "#tech",
            "#startup",
            "#saas",
            "#app",
            "#productivity",
            "#nocode",
            "#indiehackers",
            "#buildinpublic",
            "#MVP",
        ]

        for hashtag in tech_hashtags:
            try:
                hashtag_posts = await self.scrape_hashtags([hashtag])
                posts.extend(hashtag_posts[:3])  # Top 3 per hashtag

                # Rate limiting
                await self._rate_limit_delay()

            except Exception as e:
                logger.error(f"Error scraping hashtag {hashtag}: {e}")

        return posts

    async def search_opportunities(self, query: str) -> List[ScrapedPost]:
        """Search for specific opportunity signals."""
        posts = []

        # Opportunity signal keywords
        opportunity_queries = [
            '"I wish there was an app"',
            '"looking for" software tool',
            '"need help with" automation',
            '"is there a way to" automate',
            '"someone should build" tool',
            '"pain point" workflow',
            '"frustrated with" process',
        ]

        # Combine with the main query
        for opp_query in opportunity_queries[:3]:  # Limit to prevent rate limiting
            search_query = f"{query} {opp_query} -is:retweet lang:en"

            try:
                tweets = await self._search_tweets(search_query, max_results=10)
                posts.extend(tweets)

                await self._rate_limit_delay()

            except Exception as e:
                logger.error(
                    f"Error searching opportunities with query '{search_query}': {e}"
                )

        return posts

    async def detect_viral_content(self) -> List[Dict]:
        """Detect viral tweets about apps/products."""
        viral_content = []

        # Search for recent viral content about apps/products
        viral_queries = [
            "this app changed my life min_likes:1000 min_retweets:500",
            "finally found the perfect tool min_likes:500 min_retweets:200",
            "game changer for productivity min_likes:1000 min_retweets:300",
        ]

        for query in viral_queries:
            try:
                tweets = await self._search_tweets(query, max_results=5)

                for tweet in tweets:
                    # Calculate viral coefficient
                    viral_score = self._calculate_viral_score(tweet)

                    viral_content.append(
                        {
                            "tweet": tweet,
                            "viral_score": viral_score,
                            "viral_potential": "high"
                            if viral_score > 0.8
                            else "medium"
                            if viral_score > 0.5
                            else "low",
                        }
                    )

                await self._rate_limit_delay()

            except Exception as e:
                logger.error(f"Error detecting viral content: {e}")

        return viral_content

    async def scrape_hashtags(self, hashtags: List[str]) -> List[ScrapedPost]:
        """Scrape specific hashtags for opportunities."""
        posts = []

        for hashtag in hashtags:
            try:
                # Format hashtag for Twitter API
                if not hashtag.startswith("#"):
                    hashtag = f"#{hashtag}"

                query = f"{hashtag} -is:retweet lang:en"
                tweets = await self._search_tweets(query, max_results=15)
                posts.extend(tweets)

            except Exception as e:
                logger.error(f"Error scraping hashtag {hashtag}: {e}")

        return posts

    async def _search_tweets(
        self, query: str, max_results: int = 10
    ) -> List[ScrapedPost]:
        """Search tweets using Twitter API v2."""
        if not self.config.bearer_token:
            logger.warning("No Twitter Bearer Token configured, using mock data")
            return self._get_mock_tweets(query, max_results)

        posts = []

        try:
            headers = {
                "Authorization": f"Bearer {self.config.bearer_token}",
                "Content-Type": "application/json",
            }

            params = {
                "query": query,
                "max_results": min(max_results, 100),
                "tweet.fields": "created_at,author_id,public_metrics,context_annotations",
                "expansions": "author_id",
                "user.fields": "username,name,public_metrics",
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.config.api_base_url}/tweets/search/recent",
                    headers=headers,
                    params=params,
                    timeout=30.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    posts = self._process_tweet_data(data)
                else:
                    logger.error(
                        f"Twitter API error: {response.status_code} - {response.text}"
                    )

        except Exception as e:
            logger.error(f"Error searching tweets: {e}")
            # Fallback to mock data
            posts = self._get_mock_tweets(query, max_results)

        return posts

    def _process_tweet_data(self, data: Dict) -> List[ScrapedPost]:
        """Process Twitter API response into ScrapedPost objects."""
        posts = []

        if "data" not in data:
            return posts

        users = {user["id"]: user for user in data.get("includes", {}).get("users", [])}

        for tweet in data["data"]:
            try:
                author_info = users.get(tweet.get("author_id"))
                author = f"@{author_info['username']}" if author_info else None
                author_name = author_info["name"] if author_info else None

                # Extract engagement metrics
                metrics = tweet.get("public_metrics", {})
                engagement = (
                    metrics.get("like_count", 0)
                    + metrics.get("retweet_count", 0)
                    + metrics.get("reply_count", 0)
                    + metrics.get("quote_count", 0)
                )

                # Parse created_at
                created_at_str = tweet.get("created_at")
                created_at = (
                    datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                    if created_at_str
                    else None
                )

                # Create URL
                tweet_id = tweet.get("id")
                url = (
                    f"https://twitter.com/twitter/status/{tweet_id}"
                    if tweet_id
                    else None
                )

                # Filter for opportunity signals
                content = tweet.get("text", "")
                if self._is_opportunity_signal(content):
                    posts.append(
                        ScrapedPost(
                            source=self.name,
                            external_id=tweet_id or f"mock_{hash(content)}",
                            content=content,
                            author=f"{author_name} {author}"
                            if author_name and author
                            else author,
                            url=url,
                            engagement=engagement,
                            created_at=created_at,
                        )
                    )

            except Exception as e:
                logger.error(f"Error processing tweet: {e}")

        return posts

    def _is_opportunity_signal(self, content: str) -> bool:
        """Check if content contains opportunity signals."""
        opportunity_patterns = [
            r"i wish there was",
            r"looking for.*tool",
            r"need.*app that",
            r"someone should build",
            r"pain point",
            r"frustrated with",
            r"this is so hard",
            r"why isn't there",
            r"would pay for",
            r"looking for solution",
        ]

        content_lower = content.lower()
        return any(
            re.search(pattern, content_lower) for pattern in opportunity_patterns
        )

    def _calculate_viral_score(self, post: ScrapedPost) -> float:
        """Calculate viral potential score based on engagement and content."""
        # Base score from engagement rate
        base_score = min(post.engagement / 1000, 1.0)  # Normalize to 0-1

        # Boost for viral keywords
        viral_keywords = [
            "game changer",
            "life changing",
            "finally found",
            "amazing tool",
            "perfect solution",
        ]
        content_lower = post.content.lower()

        keyword_boost = (
            sum(1 for keyword in viral_keywords if keyword in content_lower) * 0.1
        )

        # Recent posts get higher scores
        recency_boost = 0.0
        if post.created_at:
            hours_ago = (
                datetime.now(timezone.utc) - post.created_at.replace(tzinfo=None)
            ).total_seconds() / 3600
            if hours_ago < 24:
                recency_boost = 0.2

        final_score = min(base_score + keyword_boost + recency_boost, 1.0)
        return final_score

    async def _rate_limit_delay(self):
        """Implement rate limiting for Twitter API."""
        current_time = datetime.now(timezone.utc).timestamp()

        # Reset counter if window expired
        if current_time - self._last_request_time > self.config.rate_limit_window:
            self._request_count = 0
            self._last_request_time = current_time

        # If approaching rate limit, wait
        if self._request_count >= self.config.max_requests_per_window - 10:
            wait_time = self.config.rate_limit_window - (
                current_time - self._last_request_time
            )
            if wait_time > 0:
                logger.info(f"Rate limit approaching, waiting {wait_time:.1f} seconds")
                await asyncio.sleep(wait_time)
                self._request_count = 0
                self._last_request_time = datetime.now(timezone.utc).timestamp()

        self._request_count += 1

    def _get_mock_tweets(self, query: str, max_results: int) -> List[ScrapedPost]:
        """Generate mock tweet data when API is not available."""
        mock_posts = [
            ScrapedPost(
                source=self.name,
                external_id=f"mock_{hash(query)}_1",
                content=f"I wish there was an app that could automatically track my productivity metrics. It's so hard to measure what actually works. #productivity #tech",
                author="John Developer @johndev",
                url="https://twitter.com/johndev/status/123456789",
                engagement=156,
                created_at=datetime.now(timezone.utc) - timedelta(hours=2),
            ),
            ScrapedPost(
                source=self.name,
                external_id=f"mock_{hash(query)}_2",
                content="Looking for a tool to automate my customer support workflow. Current solutions are too expensive for startups. #SaaS #startup",
                author="Sarah Founder @sarahfounder",
                url="https://twitter.com/sarahfounder/status/123456790",
                engagement=89,
                created_at=datetime.now(timezone.utc) - timedelta(hours=4),
            ),
            ScrapedPost(
                source=self.name,
                external_id=f"mock_{hash(query)}_3",
                content="Someone should build a project management tool that actually understands how creative teams work. Everything is too corporate-focused. #buildinpublic",
                author="Mike Designer @mikedesign",
                url="https://twitter.com/mikedesign/status/123456791",
                engagement=234,
                created_at=datetime.now(timezone.utc) - timedelta(hours=6),
            ),
        ]

        return mock_posts[:max_results]

    def test(self) -> str:
        """Test the Twitter scraper connection."""
        if self.config.bearer_token:
            return f"{self.name} scraper: API token configured and ready"
        else:
            return f"{self.name} scraper: Using mock mode (no API token configured)"
