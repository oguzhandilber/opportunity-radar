"""Extended tests for ProductHunt scraper."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.scrapers.product_hunt import ProductHuntScraper, PRODUCT_HUNT_URL
from app.scrapers.base import BaseScraper, ScrapedPost


class TestProductHuntScraper:
    """Tests for ProductHuntScraper."""

    def test_scraper_name(self):
        """Test scraper name is set correctly."""
        scraper = ProductHuntScraper()
        assert scraper.name == "product_hunt"

    def test_product_hunt_url_constant(self):
        """Test Product Hunt URL constant."""
        assert PRODUCT_HUNT_URL == "https://www.producthunt.com"

    @pytest.mark.asyncio
    async def test_scrape_success(self):
        """Test successful scraping with mocked response."""
        scraper = ProductHuntScraper()

        mock_html = """
        <html>
            <div data-test="post-item">
                <h3>Amazing Product</h3>
                <p>This is an amazing product description that is quite long.</p>
                <a href="/posts/amazing-product">Link</a>
            </div>
            <div data-test="post-item">
                <h2>Another Product</h2>
                <p>Another product description that has enough content.</p>
                <a href="/posts/another">Link</a>
            </div>
        </html>
        """

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.text = mock_html
            mock_response.raise_for_status = MagicMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            posts = await scraper.scrape()

            assert isinstance(posts, list)
            mock_client.get.assert_called()

    @pytest.mark.asyncio
    async def test_scrape_fallback_to_sections(self):
        """Test scraping falls back to section elements."""
        scraper = ProductHuntScraper()

        mock_html = """
        <html>
            <section>
                <h3>Section Product</h3>
                <p>A product in a section element with enough text.</p>
                <a href="/product1">Link</a>
            </section>
        </html>
        """

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.text = mock_html
            mock_response.raise_for_status = MagicMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            posts = await scraper.scrape()
            assert isinstance(posts, list)

    @pytest.mark.asyncio
    async def test_scrape_handles_http_error(self):
        """Test scraping handles HTTP errors gracefully."""
        scraper = ProductHuntScraper()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = Exception("HTTP Error")
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            posts = await scraper.scrape()
            assert posts == []

    @pytest.mark.asyncio
    async def test_scrape_handles_connection_error(self):
        """Test scraping handles connection errors."""
        scraper = ProductHuntScraper()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=Exception("Connection failed"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            posts = await scraper.scrape()
            assert posts == []

    @pytest.mark.asyncio
    async def test_scrape_filters_short_content(self):
        """Test that short content is filtered out."""
        scraper = ProductHuntScraper()

        mock_html = """
        <html>
            <div data-test="post-item">
                <h3>X</h3>
                <p>Y</p>
            </div>
        </html>
        """

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.text = mock_html
            mock_response.raise_for_status = MagicMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            posts = await scraper.scrape()
            # Short content should be filtered out (len <= 20)
            assert len(posts) == 0

    def test_test_method_success(self):
        """Test the test() method on success."""
        scraper = ProductHuntScraper()

        async def mock_get(*args, **kwargs):
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            return mock_response

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = mock_get
            result = scraper.test()
            assert "Connected successfully" in result

    def test_test_method_failure(self):
        """Test the test() method on failure."""
        scraper = ProductHuntScraper()

        async def mock_get_error(*args, **kwargs):
            raise Exception("Connection refused")

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = mock_get_error
            result = scraper.test()
            assert "Connection failed" in result
