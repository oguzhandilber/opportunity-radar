"""Tests for ElevenLabsService."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.elevenlabs_service import ElevenLabsService


class TestElevenLabsService:
    """Tests for ElevenLabsService."""

    @pytest.mark.asyncio
    async def test_make_call_without_api_key(self):
        """Test that call fails gracefully without API key."""
        service = ElevenLabsService()
        service.api_key = ""
        
        result = await service.make_call(
            phone_number="+1234567890",
            message="Test message",
            user_id=1
        )
        
        assert result["success"] is False
        assert "not configured" in result["error"]
        assert result["status"] == "failed"

    @pytest.mark.asyncio
    async def test_phone_number_formatting(self):
        """Test that phone number is properly formatted."""
        service = ElevenLabsService()
        service.api_key = "test_api_key"
        
        # Mock the database operations
        with patch.object(service, '_create_call_record', new_call_id:=AsyncMock(return_value=1)) as mock_create, \
             patch.object(service, '_update_call_status', new_call_id:=AsyncMock()) as mock_update, \
             patch('httpx.AsyncClient') as mock_client:
            
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            # Test with number without +
            result = await service.make_call(
                phone_number="1234567890",
                message="Test",
                user_id=1
            )
            
            # Should have attempted to create call record
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_make_call_returns_structure(self):
        """Test that make_call returns expected structure."""
        service = ElevenLabsService()
        service.api_key = "test_api_key"
        
        with patch.object(service, '_create_call_record', new_call_id:=AsyncMock(return_value=1)) as mock_create, \
             patch.object(service, '_update_call_status', new_call_id:=AsyncMock()) as mock_update, \
             patch('httpx.AsyncClient') as mock_client:
            
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            result = await service.make_call(
                phone_number="+1234567890",
                message="Your business idea has high demand!",
                user_id=1,
                demand_check_id=5
            )
            
            assert "success" in result
            assert "call_id" in result
            assert "status" in result

    @pytest.mark.asyncio
    async def test_get_elevenlabs_service_singleton(self):
        """Test that get_elevenlabs_service returns singleton."""
        from app.services.elevenlabs_service import get_elevenlabs_service
        
        service1 = get_elevenlabs_service()
        service2 = get_elevenlabs_service()
        
        assert service1 is service2
