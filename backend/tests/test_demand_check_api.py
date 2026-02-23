"""Tests for Demand Check API endpoints."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from fastapi.testclient import TestClient


class TestDemandCheckAPI:
    """Tests for Demand Check API endpoints."""

    def test_demand_check_create_schema(self):
        """Test that DemandCheckCreate schema is valid."""
        from app.api.demand_check import DemandCheckCreate
        
        # Test with valid data
        req = DemandCheckCreate(
            business_idea="A SaaS platform for pet grooming appointments",
            phone_number="+1234567890",
            notify_on_high_demand=True
        )
        assert req.business_idea == "A SaaS platform for pet grooming appointments"
        assert req.phone_number == "+1234567890"
        
    def test_demand_check_create_minimal(self):
        """Test creating request with minimal data."""
        from app.api.demand_check import DemandCheckCreate
        
        req = DemandCheckCreate(business_idea="A simple app idea")
        assert req.business_idea == "A simple app idea"
        assert req.phone_number is None
        assert req.notify_on_high_demand is True

    def test_demand_check_response_schema(self):
        """Test that DemandCheckResponse schema is valid."""
        from app.api.demand_check import DemandCheckResponse
        from datetime import datetime
        
        # Test with mock data
        response = DemandCheckResponse(
            id=1,
            user_id=1,
            business_idea="Test idea",
            status="completed",
            demand_score=75.5,
            analysis_text="High demand found",
            created_at=datetime.utcnow(),
            completed_at=None
        )
        assert response.id == 1
        assert response.demand_score == 75.5

    def test_demand_check_create_validates_business_idea_min_length(self):
        """Test that business_idea has minimum length validation."""
        from app.api.demand_check import DemandCheckCreate
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            DemandCheckCreate(business_idea="Short")

    def test_demand_check_history_item_schema(self):
        """Test DemandCheckHistoryItem schema."""
        from app.api.demand_check import DemandCheckHistoryItem
        from datetime import datetime
        
        item = DemandCheckHistoryItem(
            id=1,
            business_idea="Test idea",
            status="completed",
            demand_score=80.0,
            created_at=datetime.utcnow(),
            completed_at=None
        )
        assert item.demand_score == 80.0

    @pytest.mark.asyncio
    async def test_get_demand_check_service_singleton(self):
        """Test that get_demand_checker_service returns singleton."""
        from app.services.demand_checker import get_demand_checker_service
        
        service1 = get_demand_checker_service()
        service2 = get_demand_checker_service()
        
        assert service1 is service2

    @pytest.mark.asyncio
    async def test_get_elevenlabs_service_singleton(self):
        """Test that get_elevenlabs_service returns singleton."""
        from app.services.elevenlabs_service import get_elevenlabs_service
        
        service1 = get_elevenlabs_service()
        service2 = get_elevenlabs_service()
        
        assert service1 is service2
