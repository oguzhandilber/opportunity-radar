"""IndieHackers scraper for product launches, revenue data, and opportunity discovery."""

import logging
import re
from datetime import datetime, timezone
from typing import List, Dict, Optional
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

from app.scrapers.base import BaseScraper, ScrapedPost

logger = logging.getLogger(__name__)


class IndieHackersScraper(BaseScraper):
    name = "indiehackers"

    def __init__(self):
        self.base_url = "https://www.indiehackers.com"
        self.products_url = "https://www.indiehackers.com/products"
        self.discussions_url = "https://www.indiehackers.com/discuss"
        self.launches_url = "https://www.indiehackers.com/launches"

        self.opportunity_keywords = [
            "looking for",
            "need help",
            "recommendations",
            "alternatives",
            "pain point",
            "problem",
            "issue",
            "frustrated with",
            "tools for",
            "how to",
            "best way to",
            "what do you use",
            "feature request",
            "would pay for",
            "willing to pay",
            "need a solution",
        ]

        self.revenue_keywords = [
            "$",
            "MRR",
            "ARR",
            "revenue",
            "profit",
            "earnings",
            "income",
            "making $",
            "earning $",
            "generating",
            "monthly",
            "yearly",
        ]

    async def scrape(self) -> List[ScrapedPost]:
        all_posts = []

        try:
            products = await self.scrape_products()
            all_posts.extend(products)

            launches = await self.scrape_launches()
            all_posts.extend(launches)

            discussions = await self.scrape_discussions()
            all_posts.extend(discussions)

            logger.info(f"IndieHackers scraper collected {len(all_posts)} items")

        except Exception as e:
            logger.error(f"Error in IndieHackers main scrape: {e}")

        return all_posts

    async def scrape_products(self) -> List[ScrapedPost]:
        posts = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    self.products_url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    },
                )
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")
                product_cards = self._find_product_cards(soup)

                for idx, card in enumerate(product_cards[:50]):
                    try:
                        product_data = self._extract_product_data(card)
                        if product_data:
                            post = self._create_product_post(product_data)
                            if post:
                                posts.append(post)
                    except Exception as e:
                        logger.warning(f"Error parsing product {idx}: {e}")
                        continue

            except Exception as e:
                logger.error(f"Error scraping products: {e}")

        return posts

    async def scrape_launches(self) -> List[ScrapedPost]:
        posts = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    self.launches_url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    },
                )
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")
                launch_cards = self._find_launch_cards(soup)

                for idx, card in enumerate(launch_cards[:30]):
                    try:
                        launch_data = self._extract_launch_data(card)
                        if launch_data:
                            post = self._create_launch_post(launch_data)
                            if post:
                                posts.append(post)
                    except Exception as e:
                        logger.warning(f"Error parsing launch {idx}: {e}")
                        continue

            except Exception as e:
                logger.error(f"Error scraping launches: {e}")

        return posts

    async def scrape_discussions(self) -> List[ScrapedPost]:
        posts = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    self.discussions_url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    },
                )
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")
                discussion_threads = self._find_discussion_threads(soup)

                for idx, thread in enumerate(discussion_threads[:40]):
                    try:
                        discussion_data = self._extract_discussion_data(thread)
                        if discussion_data and self._has_opportunity_signal(
                            discussion_data
                        ):
                            post = self._create_discussion_post(discussion_data)
                            if post:
                                posts.append(post)
                    except Exception as e:
                        logger.warning(f"Error parsing discussion {idx}: {e}")
                        continue

            except Exception as e:
                logger.error(f"Error scraping discussions: {e}")

        return posts

    async def scrape_revenue_data(self) -> List[Dict]:
        revenue_data = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                products = await self.scrape_products()

                for product_post in products:
                    if self._has_revenue_mention(product_post.content):
                        revenue_info = self._extract_revenue_info(product_post.content)
                        if revenue_info:
                            revenue_data.append(
                                {
                                    "source": "product",
                                    "external_id": product_post.external_id,
                                    "content": product_post.content,
                                    "revenue_data": revenue_info,
                                    "url": product_post.url,
                                }
                            )

            except Exception as e:
                logger.error(f"Error scraping revenue data: {e}")

        return revenue_data

    async def find_similar_products(self, product_name: str) -> List[Dict]:
        similar_products = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                search_url = f"{self.products_url}?search={product_name}"
                response = await client.get(
                    search_url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    },
                )
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")
                product_cards = self._find_product_cards(soup)

                for card in product_cards[:10]:
                    product_data = self._extract_product_data(card)
                    if product_data and self._is_similar_product(
                        product_name, product_data
                    ):
                        similar_products.append(
                            {
                                "name": product_data.get("name", ""),
                                "description": product_data.get("description", ""),
                                "url": product_data.get("url", ""),
                                "pricing": product_data.get("pricing", ""),
                                "similarity_score": self._calculate_similarity(
                                    product_name, product_data
                                ),
                            }
                        )

            except Exception as e:
                logger.error(f"Error finding similar products: {e}")

        return similar_products

    def _find_product_cards(self, soup: BeautifulSoup) -> List:
        selectors = [
            "div.product-card",
            "article.product",
            "div[data-test='product-card']",
            "a[href*='/products/']",
            "div[class*='product']",
            "article",
        ]

        for selector in selectors:
            cards = soup.select(selector)
            if cards:
                return cards

        return []

    def _find_launch_cards(self, soup: BeautifulSoup) -> List:
        selectors = [
            "div.launch-card",
            "article.launch",
            "div[data-test='launch-card']",
            "a[href*='/launches/']",
            "div[class*='launch']",
            "article",
        ]

        for selector in selectors:
            cards = soup.select(selector)
            if cards:
                return cards

        return []

    def _find_discussion_threads(self, soup: BeautifulSoup) -> List:
        selectors = [
            "div.thread",
            "article.discussion",
            "div[data-test='thread']",
            "a[href*='/discuss/']",
            "div[class*='thread']",
            "article",
        ]

        for selector in selectors:
            threads = soup.select(selector)
            if threads:
                return threads

        return []

    def _extract_product_data(self, card) -> Optional[Dict]:
        try:
            name_elem = (
                card.find("h2") or card.find("h3") or card.find("a", class_="title")
            )
            desc_elem = card.find("p") or card.find("div", class_="description")
            link_elem = card.find("a", href=True)

            if not name_elem:
                return None

            name = name_elem.get_text(strip=True)
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            url = link_elem.get("href", "") if link_elem else ""

            if url and not isinstance(url, str) and not str(url).startswith("http"):
                url = urljoin(self.base_url, str(url))
            elif url and isinstance(url, str) and not url.startswith("http"):
                url = urljoin(self.base_url, url)

            pricing = self._extract_pricing(card)

            return {
                "name": name,
                "description": description,
                "url": url,
                "pricing": pricing,
                "tagline": description[:100],
            }

        except Exception as e:
            logger.warning(f"Error extracting product data: {e}")
            return None

    def _extract_launch_data(self, card) -> Optional[Dict]:
        try:
            title_elem = (
                card.find("h2") or card.find("h3") or card.find("a", class_="title")
            )
            desc_elem = card.find("p") or card.find("div", class_="description")
            author_elem = card.find("span", class_="author") or card.find(
                "a", class_="user"
            )

            if not title_elem:
                return None

            title = title_elem.get_text(strip=True)
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            author = author_elem.get_text(strip=True) if author_elem else None

            engagement = self._extract_engagement(card)
            launch_score = min(10, max(1, engagement // 10))

            return {
                "title": title,
                "description": description,
                "author": author,
                "engagement": engagement,
                "launch_score": launch_score,
            }

        except Exception as e:
            logger.warning(f"Error extracting launch data: {e}")
            return None

    def _extract_discussion_data(self, thread) -> Optional[Dict]:
        try:
            title_elem = (
                thread.find("h2")
                or thread.find("h3")
                or thread.find("a", class_="title")
            )
            author_elem = thread.find("span", class_="author") or thread.find(
                "a", class_="user"
            )
            content_elem = thread.find("div", class_="content") or thread.find("p")

            if not title_elem:
                return None

            title = title_elem.get_text(strip=True)
            author = author_elem.get_text(strip=True) if author_elem else None
            content = content_elem.get_text(strip=True) if content_elem else ""

            engagement = self._extract_engagement(thread)

            return {
                "title": title,
                "author": author,
                "content": content,
                "engagement": engagement,
            }

        except Exception as e:
            logger.warning(f"Error extracting discussion data: {e}")
            return None

    def _extract_pricing(self, card) -> str:
        pricing_text = ""

        pricing_patterns = [
            r"\$\d+\/?(month|year|mo|yr)?",
            r"Free",
            r"Freemium",
            r"Trial",
            r"Starting at",
            r"From",
        ]

        text = card.get_text()
        for pattern in pricing_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                pricing_text = match.group()
                break

        return pricing_text

    def _extract_engagement(self, element) -> int:
        engagement = 0

        vote_selectors = [
            "span[class*='vote']",
            "span[class*='point']",
            "div[class*='score']",
            "[data-test='vote-count']",
        ]

        for selector in vote_selectors:
            vote_elem = element.select_one(selector)
            if vote_elem:
                vote_text = vote_elem.get_text(strip=True)
                vote_match = re.search(r"\d+", vote_text)
                if vote_match:
                    engagement += int(vote_match.group())
                break

        comment_selectors = [
            "span[class*='comment']",
            "a[href*='#comments']",
            "div[class*='reply']",
            "[data-test='comment-count']",
        ]

        for selector in comment_selectors:
            comment_elem = element.select_one(selector)
            if comment_elem:
                comment_text = comment_elem.get_text(strip=True)
                comment_match = re.search(r"\d+", comment_text)
                if comment_match:
                    engagement += int(comment_match.group())
                break

        return engagement

    def _create_product_post(self, product_data: Dict) -> Optional[ScrapedPost]:
        try:
            content = f"{product_data['name']}: {product_data['tagline']}"
            if product_data["pricing"]:
                content += f" - {product_data['pricing']}"

            return ScrapedPost(
                source=self.name,
                external_id=f"product_{self._extract_slug(product_data['url'])}",
                content=content,
                author=None,
                url=product_data["url"],
                engagement=0,
                created_at=datetime.now(timezone.utc),
            )
        except Exception as e:
            logger.warning(f"Error creating product post: {e}")
            return None

    def _create_launch_post(self, launch_data: Dict) -> Optional[ScrapedPost]:
        try:
            content = f"Launch: {launch_data['title']}. {launch_data['description']}"

            return ScrapedPost(
                source=self.name,
                external_id=f"launch_{self._extract_slug(launch_data['title'])}",
                content=content,
                author=launch_data["author"],
                url=f"{self.launches_url}",
                engagement=launch_data["engagement"],
                created_at=datetime.now(timezone.utc),
            )
        except Exception as e:
            logger.warning(f"Error creating launch post: {e}")
            return None

    def _create_discussion_post(self, discussion_data: Dict) -> Optional[ScrapedPost]:
        try:
            content = f"Discussion: {discussion_data['title']}"
            if discussion_data["content"]:
                content += f" {discussion_data['content']}"

            return ScrapedPost(
                source=self.name,
                external_id=f"discuss_{self._extract_slug(discussion_data['title'])}",
                content=content,
                author=discussion_data["author"],
                url=f"{self.discussions_url}",
                engagement=discussion_data["engagement"],
                created_at=datetime.now(timezone.utc),
            )
        except Exception as e:
            logger.warning(f"Error creating discussion post: {e}")
            return None

    def _extract_slug(self, text: str) -> str:
        if not text:
            return "unknown"

        if text.startswith("http"):
            parsed = urlparse(text)
            slug = parsed.path.split("/")[-1]
        else:
            slug = re.sub(r"[^a-zA-Z0-9]", "_", text.lower())
            slug = slug[:50]

        return slug or "unknown"

    def _has_opportunity_signal(self, data: Dict) -> bool:
        text = f"{data.get('title', '')} {data.get('content', '')}".lower()
        return any(keyword in text for keyword in self.opportunity_keywords)

    def _has_revenue_mention(self, content: str) -> bool:
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in self.revenue_keywords)

    def _extract_revenue_info(self, content: str) -> Optional[Dict]:
        revenue_patterns = [
            r"\$(\d+(?:,\d+)*)\s*(?:mrr|arr|monthly|yearly|revenue)",
            r"(?:mrr|arr)\s*\$?\s*(\d+(?:,\d+)*)",
            r"(?:making|earning|generating)\s*\$(\d+(?:,\d+)*)",
            r"revenue\s*(?:of)?\s*\$?\s*(\d+(?:,\d+)*)",
        ]

        for pattern in revenue_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                amount = match.group(1).replace(",", "")
                try:
                    amount_num = int(amount)
                    return {
                        "amount": amount_num,
                        "type": self._classify_revenue_type(content),
                        "source_text": match.group(),
                    }
                except ValueError:
                    continue

        return None

    def _classify_revenue_type(self, content: str) -> str:
        content_lower = content.lower()
        if "mrr" in content_lower or "monthly" in content_lower:
            return "MRR"
        elif "arr" in content_lower or "yearly" in content_lower:
            return "ARR"
        else:
            return "revenue"

    def _is_similar_product(self, product_name: str, product_data: Dict) -> bool:
        similarity = self._calculate_similarity(product_name, product_data)
        return similarity > 0.3

    def _calculate_similarity(self, product_name: str, product_data: Dict) -> float:
        name = product_name.lower()
        other_name = product_data.get("name", "").lower()
        other_desc = product_data.get("description", "").lower()

        name_words = set(name.split())
        other_words = set(other_name.split()) | set(other_desc.split())

        if not name_words or not other_words:
            return 0.0

        intersection = name_words & other_words
        union = name_words | other_words

        return len(intersection) / len(union) if union else 0.0

    def test(self) -> str:
        return f"{self.name} scraper is ready with comprehensive scraping capabilities"
