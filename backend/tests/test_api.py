"""Tests for API endpoints."""

import pytest
from datetime import datetime


@pytest.mark.asyncio
async def test_health_check(client):
    """Test health check endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "app" in data


@pytest.mark.asyncio
async def test_dashboard_stats_empty(client):
    """Test dashboard stats with empty database."""
    response = await client.get("/api/dashboard/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_opportunities"] == 0
    assert data["new_opportunities"] == 0
    assert data["saved_opportunities"] == 0
    assert data["total_posts_scraped"] == 0


@pytest.mark.asyncio
async def test_opportunities_list_empty(client):
    """Test opportunities list with empty database."""
    response = await client.get("/api/opportunities")
    assert response.status_code == 200
    data = response.json()
    # Paginated response format
    assert data["items"] == []
    assert data["total"] == 0
    assert "limit" in data
    assert "offset" in data
    assert "has_more" in data


@pytest.mark.asyncio
async def test_opportunity_not_found(client):
    """Test getting non-existent opportunity."""
    response = await client.get("/api/opportunities/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_scrape_status(client):
    """Test scrape status endpoint."""
    response = await client.get("/api/scrape/status")
    assert response.status_code == 200
    data = response.json()
    assert "is_running" in data
    assert data["is_running"] is False


@pytest.mark.asyncio
async def test_settings_list_empty(client):
    """Test settings list with empty database."""
    response = await client.get("/api/settings")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)


@pytest.mark.asyncio
async def test_settings_crud(client):
    """Test settings CRUD operations."""
    # Create setting
    response = await client.put(
        "/api/settings/test_key",
        json={"value": {"test": "value"}}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["key"] == "test_key"
    assert data["value"] == {"test": "value"}

    # Read setting
    response = await client.get("/api/settings/test_key")
    assert response.status_code == 200
    data = response.json()
    assert data["value"] == {"test": "value"}

    # Delete setting
    response = await client.delete("/api/settings/test_key")
    assert response.status_code == 200

    # Verify deletion
    response = await client.get("/api/settings/test_key")
    assert response.status_code == 200
    data = response.json()
    assert data["value"] is None


# Pagination Tests
class TestPagination:
    """Tests for pagination functionality."""

    @pytest.mark.asyncio
    async def test_default_pagination_params(self, client):
        """Test default pagination parameters."""
        response = await client.get("/api/opportunities")
        assert response.status_code == 200
        data = response.json()

        assert data["limit"] == 50  # Default limit
        assert data["offset"] == 0  # Default offset
        assert data["has_more"] is False  # No more items when empty

    @pytest.mark.asyncio
    async def test_custom_limit(self, client):
        """Test custom limit parameter."""
        response = await client.get("/api/opportunities?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 10

    @pytest.mark.asyncio
    async def test_custom_offset(self, client):
        """Test custom offset parameter."""
        response = await client.get("/api/opportunities?offset=5")
        assert response.status_code == 200
        data = response.json()
        assert data["offset"] == 5

    @pytest.mark.asyncio
    async def test_limit_and_offset_together(self, client):
        """Test limit and offset together."""
        response = await client.get("/api/opportunities?limit=20&offset=10")
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 20
        assert data["offset"] == 10

    @pytest.mark.asyncio
    async def test_limit_max_value(self, client):
        """Test that limit has a maximum value (200)."""
        response = await client.get("/api/opportunities?limit=200")
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 200

    @pytest.mark.asyncio
    async def test_limit_exceeds_max_rejected(self, client):
        """Test that limit exceeding max (200) is rejected."""
        response = await client.get("/api/opportunities?limit=201")
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_limit_min_value(self, client):
        """Test minimum limit value (1)."""
        response = await client.get("/api/opportunities?limit=1")
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 1

    @pytest.mark.asyncio
    async def test_limit_zero_rejected(self, client):
        """Test that limit of 0 is rejected."""
        response = await client.get("/api/opportunities?limit=0")
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_negative_limit_rejected(self, client):
        """Test that negative limit is rejected."""
        response = await client.get("/api/opportunities?limit=-1")
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_negative_offset_rejected(self, client):
        """Test that negative offset is rejected."""
        response = await client.get("/api/opportunities?offset=-1")
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_total_count_in_response(self, client):
        """Test that total count is included in response."""
        response = await client.get("/api/opportunities")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert isinstance(data["total"], int)

    @pytest.mark.asyncio
    async def test_has_more_false_when_no_items(self, client):
        """Test has_more is False when there are no items."""
        response = await client.get("/api/opportunities")
        assert response.status_code == 200
        data = response.json()
        assert data["has_more"] is False

    @pytest.mark.asyncio
    async def test_items_array_in_response(self, client):
        """Test that items array is in response."""
        response = await client.get("/api/opportunities")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)


# Filter Tests
class TestOpportunityFilters:
    """Tests for opportunity filtering."""

    @pytest.mark.asyncio
    async def test_filter_by_status(self, client):
        """Test filtering by status."""
        response = await client.get("/api/opportunities?status=new")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_filter_by_sector(self, client):
        """Test filtering by sector."""
        response = await client.get("/api/opportunities?sector=technology")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_filter_by_min_score(self, client):
        """Test filtering by minimum score."""
        response = await client.get("/api/opportunities?min_score=5.0")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_min_score_validation(self, client):
        """Test min_score validation (0-10 range)."""
        # Valid range
        response = await client.get("/api/opportunities?min_score=0")
        assert response.status_code == 200

        response = await client.get("/api/opportunities?min_score=10")
        assert response.status_code == 200

        # Invalid - above 10
        response = await client.get("/api/opportunities?min_score=11")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_search_query(self, client):
        """Test search query parameter."""
        response = await client.get("/api/opportunities?search=test")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_search_max_length(self, client):
        """Test search query max length validation."""
        long_search = "a" * 201  # Over 200 char limit
        response = await client.get(f"/api/opportunities?search={long_search}")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_filter_by_source(self, client):
        """Test filtering by source platform."""
        response = await client.get("/api/opportunities?source=reddit")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_combined_filters(self, client):
        """Test multiple filters combined."""
        response = await client.get(
            "/api/opportunities?status=new&min_score=3&limit=10"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 10
