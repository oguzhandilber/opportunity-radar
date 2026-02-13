"""Reddit scraper using public JSON API (no authentication required)."""

import asyncio
import logging
from datetime import datetime

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import get_settings
from app.scrapers.base import BaseScraper, ScrapedPost

logger = logging.getLogger(__name__)
settings = get_settings()

# Subreddits to monitor
# Idea-focused subreddits - include all posts (they're all opportunities by definition)
IDEA_SUBREDDITS = [
    "SomebodyMakeThis",
    "AppIdeas",
    "Startup_Ideas",
    "SideProject",
    "indiehackers",
    "buildinpublic",
    "growmybusiness",
    "IMadeThis",
    "InternetIsBeautiful",
    "AlphaandBetausers",
    "RoastMyStartup",
    "hwstartups",
    "Lightbulb",
]

# General subreddits - filter by opportunity keywords
GENERAL_SUBREDDITS = [
    # Business & Entrepreneurship
    "smallbusiness",
    "Entrepreneur",
    "startups",
    "business",
    "sweatystartup",
    "EntrepreneurRideAlong",
    "juststart",
    "dropship",
    "FulfillmentByAmazon",
    "AmazonSeller",
    "ecommerce",
    "shopify",
    "WooCommerce",

    # Freelance & Remote Work
    "freelance",
    "freelanceWriters",
    "forhire",
    "WorkOnline",
    "digitalnomad",
    "remotework",
    "Upwork",
    "BeermoneyCommunity",

    # Tech & Development
    "webdev",
    "web_design",
    "Frontend",
    "reactjs",
    "nextjs",
    "node",
    "Python",
    "learnprogramming",
    "cscareerquestions",
    "experienceddevs",
    "programming",
    "softwaredevelopment",
    "SaaS",
    "nocode",
    "lowcode",
    "Automate",
    "selfhosted",
    "homelab",
    "devops",
    "aws",
    "googlecloud",
    "Azure",
    "kubernetes",
    "docker",

    # AI & Machine Learning
    "MachineLearning",
    "artificial",
    "LocalLLaMA",
    "ChatGPT",
    "OpenAI",
    "StableDiffusion",
    "singularity",
    "MLQuestions",

    # Marketing & Growth
    "marketing",
    "digital_marketing",
    "SEO",
    "PPC",
    "socialmedia",
    "content_marketing",
    "copywriting",
    "Emailmarketing",
    "GrowthHacking",
    "analytics",
    "bigseo",
    "affiliatemarketing",

    # Design & Creative
    "design",
    "graphic_design",
    "UI_Design",
    "userexperience",
    "web_design",
    "logodesign",
    "DesignJobs",

    # Finance & Investing
    "personalfinance",
    "financialindependence",
    "fatFIRE",
    "investing",
    "stocks",
    "CryptoCurrency",
    "Bitcoin",
    "ethereum",
    "defi",
    "Bogleheads",
    "realestateinvesting",
    "RealEstate",
    "tax",
    "Accounting",
    "smallbusinessuk",

    # Professional & Career
    "sales",
    "recruiting",
    "jobs",
    "careerguidance",
    "resumes",
    "interviews",
    "managers",
    "consulting",
    "lawfirm",
    "medicine",
    "Dentistry",
    "physicaltherapy",
    "veterinary",

    # Productivity & Tools
    "productivity",
    "getdisciplined",
    "Notion",
    "ObsidianMD",
    "Airtable",
    "shortcuts",
    "IFTTT",
    "Zapier",
    "automation",
    "QuantifiedSelf",

    # Education & Learning
    "education",
    "Teachers",
    "OnlineEducation",
    "languagelearning",
    "learnspanish",
    "learnfrench",
    "learnpython",
    "courses",
    "college",
    "GradSchool",
    "PhD",

    # Health & Fitness
    "Fitness",
    "loseit",
    "gainit",
    "nutrition",
    "MealPrepSunday",
    "keto",
    "intermittentfasting",
    "running",
    "bodyweightfitness",
    "homegym",
    "yoga",
    "Meditation",
    "mentalhealth",
    "Anxiety",
    "depression",
    "ADHD",
    "sleep",

    # Home & Lifestyle
    "HomeImprovement",
    "DIY",
    "homeowners",
    "HomeDecorating",
    "InteriorDesign",
    "malelivingspace",
    "femalelivingspace",
    "organization",
    "declutter",
    "minimalism",
    "BuyItForLife",
    "Frugal",

    # Parenting & Family
    "Parenting",
    "Mommit",
    "daddit",
    "beyondthebump",
    "NewParents",
    "homeschool",
    "Nanny",
    "AuPairs",

    # Food & Cooking
    "Cooking",
    "recipes",
    "MealPrepSunday",
    "EatCheapAndHealthy",
    "slowcooking",
    "Baking",
    "Breadit",
    "Coffee",
    "tea",
    "cocktails",
    "fermentation",
    "foodhacks",

    # Hobbies & Interests
    "gardening",
    "IndoorGarden",
    "houseplants",
    "Aquariums",
    "photography",
    "videography",
    "Filmmakers",
    "podcasting",
    "streaming",
    "gaming",
    "gamedev",
    "boardgames",
    "woodworking",
    "metalworking",
    "3Dprinting",
    "crafts",
    "crochet",
    "knitting",
    "sewing",
    "leathercraft",
    "jewelry",
    "camping",
    "hiking",
    "bicycling",
    "MTB",
    "motorcycles",
    "cars",
    "CarTalkUK",
    "AutoDetailing",

    # Pets
    "dogs",
    "cats",
    "Pets",
    "DogTraining",
    "puppy101",
    "CatAdvice",
    "AquariumAdvice",

    # Travel
    "travel",
    "solotravel",
    "TravelHacks",
    "backpacking",
    "Shoestring",
    "awardtravel",
    "churning",

    # Events & Weddings
    "weddingplanning",
    "Weddings",
    "wedding",
    "EventProfs",

    # Local/Regional
    "Turkey",
    "istanbul",
    "europe",
    "london",
    "nyc",
    "sanfrancisco",
    "LosAngeles",
    "chicago",
    "Austin",
    "Seattle",
    "boston",
    "toronto",
    "vancouver",
    "sydney",
    "melbourne",

    # Niche Industries
    "legaladvice",
    "Insurance",
    "healthcare",
    "nursing",
    "pharmacy",
    "Construction",
    "HVAC",
    "Plumbing",
    "Electricians",
    "Roofing",
    "Landscaping",
    "lawncare",
    "AutoMechanics",
    "MechanicAdvice",
    "Truckers",
    "logistics",
    "supplychain",
    "restaurateur",
    "KitchenConfidential",
    "bartenders",
    "Barber",
    "hairdresser",
    "Estheticians",
    "tattoos",
    "TattooArtists",
    "photography",
    "WeddingPhotography",
    "videography",
    "VoiceActing",
    "acting",
    "Screenwriting",
    "filmmaking",
    "WeAreTheMusicMakers",
    "audioengineering",
    "podcasting",

    # Gaming & Entertainment
    "gaming",
    "pcgaming",
    "Games",
    "indiegaming",
    "gamedev",
    "Unity3D",
    "unrealengine",
    "Steam",
    "NintendoSwitch",
    "PS5",
    "XboxSeriesX",
    "VRGaming",
    "Twitch",
    "youtube",
    "NewTubers",

    # Specific Pain Points
    "TechSupport",
    "sysadmin",
    "networking",
    "datahoarder",
    "privacy",
    "VPN",
    "cybersecurity",
    "netsec",
    "AskEngineers",
    "AskProgramming",
    "webhosting",
    "Wordpress",
    "Squarespace",
    "wix",
]

# Keywords that indicate opportunity signals
# Organized by signal strength (Tier 1 = highest intent)
OPPORTUNITY_KEYWORDS = [
    # === TIER 1: GOLD KEYWORDS (Highest Signal) ===
    # Direct payment intent
    "I'd pay for",
    "would pay for",
    "take my money",
    "shut up and take my money",
    "willing to pay",
    "ready to pay",
    "I'm paying",
    "paying $",

    # Strong desire signals
    "I wish there was",
    "why doesn't anyone",
    "someone should make",
    "why isn't there",
    "there should be",
    "why can't I",

    # Extreme frustration (high pain = high value)
    "drives me crazy",
    "losing my mind",
    "so frustrated",
    "can't stand",
    "hate dealing with",
    "sick of",
    "fed up with",

    # === TIER 2: PROBLEM SIGNALS ===
    # Direct requests
    "is there an app for",
    "looking for a tool",
    "can't find any",
    "frustrated with",
    "any alternatives to",
    "need a solution",

    # Pain points
    "hate using",
    "tired of",
    "annoyed by",
    "struggling with",
    "pain point",
    "biggest challenge",
    "biggest problem",
    "waste of time",
    "too expensive",
    "too complicated",
    "doesn't work",
    "broken",
    "buggy",
    "unreliable",
    "slow",
    "clunky",

    # === TIER 3: SOLUTION SEEKING ===
    "looking for",
    "searching for",
    "need help with",
    "any recommendations",
    "what do you use for",
    "how do you handle",
    "best way to",
    "better way to",
    "easier way to",
    "how to automate",
    "how to streamline",
    "any tools for",

    # === TIER 4: SWITCHING INTENT ===
    "switching from",
    "moving away from",
    "leaving",
    "cancelling",
    "alternative to",
    "replacement for",
    "instead of",
    "better than",
    "cheaper than",
    "migrating from",

    # === TIER 5: BUILDING/VALIDATION ===
    "thinking of building",
    "want to build",
    "planning to create",
    "working on",
    "building a",
    "creating a",
    "developing a",
    "launching",
    "would anyone use",
    "is there a market",
    "would people pay",
    "validate my idea",
    "feedback on my idea",
    "does this exist",
    "has anyone tried",

    # === TIER 6: BUDGET/PRICING SIGNALS ===
    "budget",
    "pricing",
    "cost",
    "subscription",
    "monthly fee",
    "one-time payment",
    "free trial",
    "freemium",
    "enterprise",

    # === TURKISH KEYWORDS ===
    "arıyorum",
    "lazım",
    "ihtiyacım var",
    "önerir misiniz",
    "alternatif",
    "çözüm",
    "sorun yaşıyorum",
    "problem",
    "bıktım",
    "sıkıldım",
    "keşke olsa",
    "neden yok",
    "öderdim",
    "para veririm",
]

# Additional high-value subreddits (from the article analysis)
EXTRA_SUBREDDITS = [
    "Etsy",  # E-commerce seller problems (800K)
    "passive_income",  # Income seekers
    "juststart",  # New entrepreneurs
    "microsaas",  # Micro SaaS builders
    "EntrepreneurRideAlong",  # Entrepreneur journey
    "SAHP",  # Stay at home parents
    "antiwork",  # Work frustrations
    "workreform",  # Work problems
    "cscareerquestionsEU",  # EU tech jobs
]

# Combined list of all subreddits to monitor
SUBREDDITS = IDEA_SUBREDDITS + GENERAL_SUBREDDITS + EXTRA_SUBREDDITS

# User agent for public API access
USER_AGENT = "OpportunityRadar/1.0 (Educational/Research Bot)"


class RedditScraper(BaseScraper):
    """Scraper for Reddit using public JSON API (no API key required)."""

    name = "reddit"

    # Minimum engagement to fetch comments for a post
    MIN_ENGAGEMENT_FOR_COMMENTS = 10
    # Maximum comments to extract per post
    MAX_COMMENTS_PER_POST = 20
    # Maximum comment depth to traverse
    MAX_COMMENT_DEPTH = 5

    def __init__(self):
        self._rate_limit_delay = max(2.0, settings.request_delay_seconds)  # Min 2s for public API

    async def scrape(self) -> list[ScrapedPost]:
        """Scrape posts and comments from Reddit subreddits."""
        all_posts = []
        successful = 0
        failed = 0
        seen_ids = set()  # Avoid duplicates
        comments_extracted = 0

        logger.info(f"Starting Reddit scrape of {len(SUBREDDITS)} subreddits (public JSON API)")

        async with httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT},
            timeout=30.0,
            follow_redirects=True,
        ) as client:
            for i, subreddit_name in enumerate(SUBREDDITS):
                try:
                    # Fetch both hot and new posts for more coverage
                    for sort_type in ["hot", "new"]:
                        posts = await self._fetch_subreddit_posts(client, subreddit_name, sort_type, seen_ids)

                        # For high-engagement posts, also fetch comments
                        for post in posts:
                            if post.engagement >= self.MIN_ENGAGEMENT_FOR_COMMENTS:
                                comment_posts = await self._fetch_post_comments(
                                    client, post.url, post.external_id, seen_ids
                                )
                                all_posts.extend(comment_posts)
                                comments_extracted += len(comment_posts)
                                for cp in comment_posts:
                                    seen_ids.add(cp.external_id)

                                # Small delay between comment fetches
                                await asyncio.sleep(1.0)

                        all_posts.extend(posts)
                        for p in posts:
                            seen_ids.add(p.external_id)

                    successful += 1

                    # Rate limiting between subreddits (public API needs more delay)
                    if i < len(SUBREDDITS) - 1:
                        await asyncio.sleep(self._rate_limit_delay)

                except Exception as e:
                    failed += 1
                    logger.error(f"Error scraping r/{subreddit_name}: {e}")
                    continue

        logger.info(
            f"Reddit scrape complete: {len(all_posts)} items "
            f"({len(all_posts) - comments_extracted} posts + {comments_extracted} comments) "
            f"from {successful}/{len(SUBREDDITS)} subreddits"
        )
        return all_posts

    async def _fetch_post_comments(
        self, client: httpx.AsyncClient, post_url: str, post_id: str, seen_ids: set
    ) -> list[ScrapedPost]:
        """Fetch comments from a single post thread."""
        comments = []

        # Convert post URL to JSON endpoint
        # https://reddit.com/r/sub/comments/abc123/title/ -> https://reddit.com/r/sub/comments/abc123.json
        json_url = post_url.rstrip("/") + ".json"

        try:
            response = await client.get(json_url, params={"raw_json": 1, "limit": 100})

            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 30))
                logger.warning(f"Rate limited fetching comments, waiting {retry_after}s")
                await asyncio.sleep(retry_after)
                response = await client.get(json_url, params={"raw_json": 1, "limit": 100})

            if response.status_code not in (200,):
                return []

            data = response.json()

            # Reddit returns [post_data, comments_data]
            if not isinstance(data, list) or len(data) < 2:
                return []

            comments_data = data[1].get("data", {}).get("children", [])

            # Recursively extract comments
            self._extract_comments(
                comments_data,
                comments,
                seen_ids,
                post_id,
                depth=0
            )

            if comments:
                logger.debug(f"Extracted {len(comments)} valuable comments from post {post_id}")

        except Exception as e:
            logger.debug(f"Error fetching comments for {post_id}: {e}")

        return comments[:self.MAX_COMMENTS_PER_POST]

    def _extract_comments(
        self,
        children: list,
        results: list,
        seen_ids: set,
        parent_post_id: str,
        depth: int = 0
    ) -> None:
        """Recursively extract comments with opportunity signals."""
        if depth > self.MAX_COMMENT_DEPTH:
            return

        for child in children:
            if child.get("kind") != "t1":  # t1 = comment
                continue

            comment_data = child.get("data", {})
            comment_id = comment_data.get("id", "")

            # Skip already seen
            if comment_id in seen_ids or f"comment_{comment_id}" in seen_ids:
                continue

            body = comment_data.get("body", "")
            author = comment_data.get("author")
            score = comment_data.get("score", 0)

            if author in ("[deleted]", None):
                author = None

            # Only include comments with opportunity signals
            if body and self._has_opportunity_signal(body):
                results.append(
                    ScrapedPost(
                        source=f"{self.name}_comment",
                        external_id=f"comment_{comment_id}",
                        content=body,
                        author=author,
                        url=f"https://reddit.com{comment_data.get('permalink', '')}",
                        engagement=score,
                        created_at=datetime.fromtimestamp(comment_data.get("created_utc", 0)),
                    )
                )

            # Process nested replies
            replies = comment_data.get("replies")
            if replies and isinstance(replies, dict):
                reply_children = replies.get("data", {}).get("children", [])
                self._extract_comments(
                    reply_children,
                    results,
                    seen_ids,
                    parent_post_id,
                    depth + 1
                )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
        before_sleep=lambda retry_state: logger.warning(
            f"Reddit API retry attempt {retry_state.attempt_number} after error"
        ),
    )
    async def _fetch_subreddit_posts(
        self, client: httpx.AsyncClient, subreddit_name: str, sort_type: str = "hot", seen_ids: set = None
    ) -> list[ScrapedPost]:
        """Fetch posts from a single subreddit using public JSON API."""
        posts = []
        seen_ids = seen_ids or set()
        limit = max(1, settings.max_posts_per_source // len(SUBREDDITS))

        # Idea-focused subreddits include all posts (they're opportunities by definition)
        is_idea_subreddit = subreddit_name in IDEA_SUBREDDITS

        url = f"https://www.reddit.com/r/{subreddit_name}/{sort_type}.json"
        params = {"limit": limit, "raw_json": 1}

        try:
            response = await client.get(url, params=params)

            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                logger.warning(f"Rate limited by Reddit, waiting {retry_after}s")
                await asyncio.sleep(retry_after)
                response = await client.get(url, params=params)

            # Handle private/banned subreddits
            if response.status_code in (403, 404):
                logger.warning(f"Subreddit r/{subreddit_name} is private, banned, or doesn't exist")
                return []

            response.raise_for_status()
            data = response.json()

            for child in data.get("data", {}).get("children", []):
                post = child.get("data", {})
                post_id = post.get("id", "")

                if post.get("stickied"):  # Skip pinned posts
                    continue

                # Skip already seen posts (from other sort types)
                if post_id in seen_ids:
                    continue

                # Get author (may be deleted)
                author = post.get("author")
                if author in ("[deleted]", None):
                    author = None

                title = post.get("title", "")
                selftext = post.get("selftext", "")
                content = f"{title}\n\n{selftext}"

                # Include post if: idea subreddit OR has opportunity signal
                if is_idea_subreddit or self._has_opportunity_signal(content):
                    posts.append(
                        ScrapedPost(
                            source=self.name,
                            external_id=post_id,
                            content=content,
                            author=author,
                            url=f"https://reddit.com{post.get('permalink', '')}",
                            engagement=post.get("score", 0) + post.get("num_comments", 0),
                            created_at=datetime.fromtimestamp(post.get("created_utc", 0)),
                        )
                    )

        except httpx.HTTPStatusError as e:
            error_str = str(e).lower()
            if "403" in error_str or "404" in error_str:
                logger.warning(f"Subreddit r/{subreddit_name} is private or banned, skipping")
            else:
                raise

        return posts

    def _has_opportunity_signal(self, content: str) -> bool:
        """Check if content contains opportunity-related keywords."""
        content_lower = content.lower()
        return any(keyword.lower() in content_lower for keyword in OPPORTUNITY_KEYWORDS)

    def test(self) -> str:
        """Test Reddit public API connection."""
        import asyncio

        async def _test():
            try:
                async with httpx.AsyncClient(
                    headers={"User-Agent": USER_AGENT},
                    timeout=10.0,
                    follow_redirects=True,
                ) as client:
                    response = await client.get(
                        "https://www.reddit.com/r/test/hot.json",
                        params={"limit": 1}
                    )
                    response.raise_for_status()
                    data = response.json()
                    if "data" in data:
                        logger.info("Reddit public API connection test successful")
                        return f"{self.name} scraper: Connected successfully (public API, no auth required)"
                    return f"{self.name} scraper: Unexpected response format"
            except Exception as e:
                logger.error(f"Reddit connection failed: {e}")
                return f"{self.name} scraper: Connection failed - {e}"

        # Run async test
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            # If already in async context, create task
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, _test())
                return future.result()
        else:
            return loop.run_until_complete(_test())
