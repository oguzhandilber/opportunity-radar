"""Tests for DemandCheckRequest model."""

import pytest
from datetime import datetime

from app.models.app_store import DemandCheckRequest


class TestDemandCheckRequest:
    """Tests for DemandCheckRequest model."""

    @pytest.mark.asyncio
    async def test_create_demand_check_request(self, db_session):
        """Test creating a demand check request."""
        request = DemandCheckRequest(
            user_id=1,
            business_idea="A SaaS platform for pet grooming appointment scheduling",
            status="pending",
        )
        db_session.add(request)
        await db_session.commit()
        await db_session.refresh(request)

        assert request.id is not None
        assert request.user_id == 1
        assert request.business_idea == "A SaaS platform for pet grooming appointment scheduling"
        assert request.status == "pending"
        assert request.demand_score is None
        assert request.created_at is not None

    @pytest.mark.asyncio
    async def test_demand_check_request_with_results(self, db_session):
        """Test demand check request with completed results."""
        request = DemandCheckRequest(
            user_id=1,
            business_idea="AI-powered recipe generator",
            status="completed",
            demand_score=8.5,
            analysis_text="High demand in health & fitness category",
        )
        db_session.add(request)
        await db_session.commit()
        await db_session.refresh(request)

        assert request.id is not None
        assert request.status == "completed"
        assert request.demand_score == 8.5
        assert request.analysis_text == "High demand in health & fitness category"

    @pytest.mark.asyncio
    async def test_demand_check_request_status_values(self, db_session):
        """Test different status values."""
        # Pending
        pending_req = DemandCheckRequest(
            user_id=1,
            business_idea="Test idea",
            status="pending",
        )
        db_session.add(pending_req)
        await db_session.commit()

        # Completed
        completed_req = DemandCheckRequest(
            user_id=1,
            business_idea="Test idea 2",
            status="completed",
        )
        db_session.add(completed_req)
        await db_session.commit()

        # Failed
        failed_req = DemandCheckRequest(
            user_id=1,
            business_idea="Test idea 3",
            status="failed",
        )
        db_session.add(failed_req)
        await db_session.commit()

        assert pending_req.status == "pending"
        assert completed_req.status == "completed"
        assert failed_req.status == "failed"

    @pytest.mark.asyncio
    async def test_demand_check_request_timestamps(self, db_session):
        """Test that timestamps are automatically set."""
        before = datetime.utcnow()
        request = DemandCheckRequest(
            user_id=1,
            business_idea="Test idea",
            status="pending",
        )
        db_session.add(request)
        await db_session.commit()
        await db_session.refresh(request)
        after = datetime.utcnow()

        assert request.created_at is not None
        assert request.created_at >= before
        assert request.created_at <= after
