"""Tests for CallHistory model."""

import pytest
from datetime import datetime

from app.models.app_store import CallHistory


class TestCallHistory:
    """Tests for CallHistory model."""

    @pytest.mark.asyncio
    async def test_create_call_history(self, db_session):
        """Test creating a call history record."""
        call = CallHistory(
            user_id=1,
            status="initiated",
        )
        db_session.add(call)
        await db_session.commit()
        await db_session.refresh(call)

        assert call.id is not None
        assert call.user_id == 1
        assert call.status == "initiated"
        assert call.created_at is not None

    @pytest.mark.asyncio
    async def test_call_history_with_elevenlabs_id(self, db_session):
        """Test call history with ElevenLabs call ID."""
        call = CallHistory(
            user_id=1,
            elevenlabs_call_id="call_abc123xyz",
            status="completed",
            duration_seconds=45,
        )
        db_session.add(call)
        await db_session.commit()
        await db_session.refresh(call)

        assert call.id is not None
        assert call.elevenlabs_call_id == "call_abc123xyz"
        assert call.status == "completed"
        assert call.duration_seconds == 45

    @pytest.mark.asyncio
    async def test_call_history_linked_to_demand_check(self, db_session):
        """Test call history linked to a demand check request."""
        from app.models.app_store import DemandCheckRequest
        
        # Create a demand check request first
        demand_check = DemandCheckRequest(
            user_id=1,
            business_idea="Test idea",
            status="completed",
            demand_score=8.0,
        )
        db_session.add(demand_check)
        await db_session.commit()
        await db_session.refresh(demand_check)
        
        # Create call linked to demand check
        call = CallHistory(
            user_id=1,
            demand_check_id=demand_check.id,
            elevenlabs_call_id="call_xyz789",
            status="completed",
            duration_seconds=30,
        )
        db_session.add(call)
        await db_session.commit()
        await db_session.refresh(call)

        assert call.demand_check_id == demand_check.id
        assert call.demand_check.business_idea == "Test idea"

    @pytest.mark.asyncio
    async def test_call_history_status_values(self, db_session):
        """Test different status values."""
        initiated = CallHistory(user_id=1, status="initiated")
        completed = CallHistory(user_id=1, status="completed")
        failed = CallHistory(user_id=1, status="failed")
        
        db_session.add(initiated)
        db_session.add(completed)
        db_session.add(failed)
        await db_session.commit()

        assert initiated.status == "initiated"
        assert completed.status == "completed"
        assert failed.status == "failed"
