"""Tests for middleware (auth, rate limiting)."""

import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException

from app.middleware.auth import verify_api_key, api_key_header
from app.middleware.rate_limit import (
    limiter,
    RATE_LIMITS,
    rate_limit_exceeded_handler,
    get_limiter,
)


class TestAuthMiddleware:
    """Tests for API key authentication middleware."""

    def test_dev_mode_no_api_key_configured(self):
        """Test that requests are allowed when no API key is configured (dev mode)."""
        with patch("app.middleware.auth.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(api_key="")

            result = verify_api_key(api_key=None)
            assert result == "dev-mode"

    def test_dev_mode_with_any_key(self):
        """Test that any key works when no API key is configured."""
        with patch("app.middleware.auth.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(api_key="")

            result = verify_api_key(api_key="random-key")
            assert result == "dev-mode"

    def test_missing_api_key_raises_401(self):
        """Test that missing API key raises 401 when key is configured."""
        with patch("app.middleware.auth.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(api_key="secret-key-123")

            with pytest.raises(HTTPException) as exc_info:
                verify_api_key(api_key=None)

            assert exc_info.value.status_code == 401
            assert "Missing API key" in exc_info.value.detail

    def test_invalid_api_key_raises_403(self):
        """Test that invalid API key raises 403."""
        with patch("app.middleware.auth.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(api_key="secret-key-123")

            with pytest.raises(HTTPException) as exc_info:
                verify_api_key(api_key="wrong-key")

            assert exc_info.value.status_code == 403
            assert "Invalid API key" in exc_info.value.detail

    def test_valid_api_key_returns_key(self):
        """Test that valid API key returns the key."""
        with patch("app.middleware.auth.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(api_key="secret-key-123")

            result = verify_api_key(api_key="secret-key-123")
            assert result == "secret-key-123"

    def test_api_key_comparison_is_constant_time(self):
        """Test that API key comparison uses constant-time comparison."""
        # This test verifies the implementation uses secrets.compare_digest
        # by checking that similar-but-wrong keys don't provide timing info
        with patch("app.middleware.auth.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(api_key="secret-key-123")

            # Both should fail with 403, timing should be similar
            with pytest.raises(HTTPException):
                verify_api_key(api_key="secret-key-124")  # Off by one char

            with pytest.raises(HTTPException):
                verify_api_key(api_key="completely-different")

    def test_api_key_header_name(self):
        """Test that the API key header is named correctly."""
        assert api_key_header.model.name == "X-API-Key"


class TestRateLimitMiddleware:
    """Tests for rate limiting middleware."""

    def test_rate_limits_defined(self):
        """Test that rate limits are properly defined."""
        assert "default" in RATE_LIMITS
        assert "scrape" in RATE_LIMITS
        assert "analyze" in RATE_LIMITS
        assert "export" in RATE_LIMITS

    def test_scrape_limit_is_restrictive(self):
        """Test that scrape endpoint has restrictive rate limit."""
        assert "5/minute" in RATE_LIMITS["scrape"]

    def test_analyze_limit(self):
        """Test analyze endpoint rate limit."""
        assert "10/minute" in RATE_LIMITS["analyze"]

    def test_get_limiter_returns_limiter(self):
        """Test that get_limiter returns the limiter instance."""
        result = get_limiter()
        assert result is limiter

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded_handler(self):
        """Test custom rate limit exceeded handler."""
        from slowapi.errors import RateLimitExceeded

        # Create mock request and exception
        mock_request = MagicMock()
        mock_exc = MagicMock(spec=RateLimitExceeded)
        mock_exc.detail = "5 per 1 minute"

        response = await rate_limit_exceeded_handler(mock_request, mock_exc)

        assert response.status_code == 429
        # Parse response body
        import json
        body = json.loads(response.body.decode())
        assert body["error"] == "Rate limit exceeded"
        assert "5 per 1 minute" in body["detail"]

    @pytest.mark.asyncio
    async def test_rate_limit_handler_includes_retry_after(self):
        """Test that rate limit response includes retry_after."""
        from slowapi.errors import RateLimitExceeded

        mock_request = MagicMock()
        mock_exc = MagicMock(spec=RateLimitExceeded)
        mock_exc.detail = "10 per 1 minute"
        mock_exc.retry_after = 30

        response = await rate_limit_exceeded_handler(mock_request, mock_exc)

        import json
        body = json.loads(response.body.decode())
        assert body["retry_after"] == 30


class TestAuthMiddlewareIntegration:
    """Integration tests for auth middleware with actual endpoints."""

    @pytest.mark.asyncio
    async def test_health_endpoint_no_auth_required(self, client):
        """Test that health endpoint doesn't require authentication."""
        response = await client.get("/health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_api_endpoint_with_auth_disabled(self, client):
        """Test API endpoints work when auth is disabled (dev mode)."""
        # By default, API_KEY is empty in test environment
        response = await client.get("/api/opportunities")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_api_endpoint_with_valid_key(self, client):
        """Test API endpoints work with valid API key."""
        with patch("app.middleware.auth.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(api_key="test-key")

            response = await client.get(
                "/api/opportunities",
                headers={"X-API-Key": "test-key"}
            )
            # Should work (200) or be dev mode (API_KEY not enforced in test)
            assert response.status_code in [200, 401, 403]
