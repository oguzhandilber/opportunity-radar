"""Tests for DemandCheckerService."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.demand_checker import DemandCheckerService


class TestDemandCheckerService:
    """Tests for DemandCheckerService."""

    @pytest.mark.asyncio
    async def test_check_demand_returns_structure(self):
        """Test that check_demand returns expected structure."""
        service = DemandCheckerService()
        
        # Mock the AI client
        service.ai_client = AsyncMock()
        service.ai_client.complete_json = AsyncMock(return_value={
            "demand_score": 75,
            "analysis_text": "High demand in productivity apps"
        })
        
        # Mock database context
        with patch('app.services.demand_checker.get_db_context') as mock_db:
            mock_context = AsyncMock()
            mock_session = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_session)
            mock_context.__aexit__ = AsyncMock()
            mock_db.return_value = mock_context
            
            # Mock category query
            mock_session.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(all=MagicMock(return_value=[]))))
            
            result = await service.check_demand("A task management app", user_id=1)
            
            assert "demand_score" in result
            assert "analysis_text" in result
            assert isinstance(result["demand_score"], (int, float))
            assert isinstance(result["analysis_text"], str)

    @pytest.mark.asyncio
    async def test_demand_score_clamped_to_0_100(self):
        """Test that demand score is clamped to 0-100 range."""
        service = DemandCheckerService()
        
        # Test with score above 100
        service.ai_client = AsyncMock()
        service.ai_client.complete_json = AsyncMock(return_value={
            "demand_score": 150,
            "analysis_text": "Test"
        })
        
        with patch('app.services.demand_checker.get_db_context') as mock_db:
            mock_context = AsyncMock()
            mock_session = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_session)
            mock_context.__aexit__ = AsyncMock()
            mock_db.return_value = mock_context
            mock_session.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(all=MagicMock(return_value=[]))))
            
            result = await service.check_demand("Test idea", user_id=1)
            
            assert result["demand_score"] <= 100

    @pytest.mark.asyncio
    async def test_demand_score_clamped_above_zero(self):
        """Test that negative scores are clamped to 0."""
        service = DemandCheckerService()
        
        service.ai_client = AsyncMock()
        service.ai_client.complete_json = AsyncMock(return_value={
            "demand_score": -10,
            "analysis_text": "Test"
        })
        
        with patch('app.services.demand_checker.get_db_context') as mock_db:
            mock_context = AsyncMock()
            mock_session = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_session)
            mock_context.__aexit__ = AsyncMock()
            mock_db.return_value = mock_context
            mock_session.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(all=MagicMock(return_value=[]))))
            
            result = await service.check_demand("Test idea", user_id=1)
            
            assert result["demand_score"] >= 0

    @pytest.mark.asyncio
    async def test_analysis_text_always_string(self):
        """Test that analysis_text is always a string."""
        service = DemandCheckerService()
        
        service.ai_client = AsyncMock()
        service.ai_client.complete_json = AsyncMock(return_value={
            "demand_score": 50,
            "analysis_text": None  # Test with None
        })
        
        with patch('app.services.demand_checker.get_db_context') as mock_db:
            mock_context = AsyncMock()
            mock_session = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_session)
            mock_context.__aexit__ = AsyncMock()
            mock_db.return_value = mock_context
            mock_session.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(all=MagicMock(return_value=[]))))
            
            result = await service.check_demand("Test idea", user_id=1)
            
            assert isinstance(result["analysis_text"], str)

    @pytest.mark.asyncio
    async def test_get_demand_checker_service_singleton(self):
        """Test that get_demand_checker_service returns singleton."""
        from app.services.demand_checker import get_demand_checker_service
        
        service1 = get_demand_checker_service()
        service2 = get_demand_checker_service()
        
        assert service1 is service2
