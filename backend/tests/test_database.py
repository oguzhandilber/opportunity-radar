"""Tests for database models."""

import pytest
from datetime import datetime

from app.database import RawPost, Opportunity, Setting


class TestRawPost:
    """Tests for RawPost model."""

    @pytest.mark.asyncio
    async def test_create_raw_post(self, db_session):
        """Test creating a raw post."""
        post = RawPost(
            source="reddit",
            external_id="abc123",
            content="Test content for opportunity",
            author="testuser",
            url="https://reddit.com/r/test/comments/abc123",
            engagement=100,
            created_at=datetime.utcnow(),
            scraped_at=datetime.utcnow(),
        )
        db_session.add(post)
        await db_session.commit()
        await db_session.refresh(post)

        assert post.id is not None
        assert post.source == "reddit"
        assert post.external_id == "abc123"

    @pytest.mark.asyncio
    async def test_unique_constraint(self, db_session):
        """Test source + external_id unique constraint."""
        from sqlalchemy.exc import IntegrityError

        post1 = RawPost(
            source="reddit",
            external_id="same_id",
            content="First post",
        )
        db_session.add(post1)
        await db_session.commit()

        post2 = RawPost(
            source="reddit",
            external_id="same_id",
            content="Duplicate post",
        )
        db_session.add(post2)

        with pytest.raises(IntegrityError):
            await db_session.commit()


class TestOpportunity:
    """Tests for Opportunity model."""

    @pytest.mark.asyncio
    async def test_create_opportunity(self, db_session):
        """Test creating an opportunity."""
        # First create a raw post
        post = RawPost(
            source="hackernews",
            external_id="hn123",
            content="Show HN: My new SaaS tool",
        )
        db_session.add(post)
        await db_session.commit()
        await db_session.refresh(post)

        # Create opportunity
        opp = Opportunity(
            raw_post_id=post.id,
            title="SaaS Tool for Small Business",
            summary="A tool that helps small businesses manage their workflow",
            product_type="SaaS",
            sector="Productivity",
            business_model="Subscription",
            demand_score=7.5,
            market_score=8.0,
            feasibility_score=6.5,
            revenue_score=7.0,
            total_score=7.25,
            confidence=0.85,
            competitors=[{"name": "Competitor A", "url": "https://competitor.com"}],
            suggested_features=[{"feature": "Dashboard", "priority": "high"}],
            go_to_market="Focus on content marketing and SEO",
            status="new",
        )
        db_session.add(opp)
        await db_session.commit()
        await db_session.refresh(opp)

        assert opp.id is not None
        assert opp.raw_post_id == post.id
        assert opp.total_score == 7.25
        assert opp.status == "new"
        assert len(opp.competitors) == 1
        assert len(opp.suggested_features) == 1

    @pytest.mark.asyncio
    async def test_opportunity_status_update(self, db_session):
        """Test updating opportunity status."""
        post = RawPost(source="test", external_id="test1", content="Test")
        db_session.add(post)
        await db_session.commit()
        await db_session.refresh(post)

        opp = Opportunity(
            raw_post_id=post.id,
            title="Test Opportunity",
            status="new",
        )
        db_session.add(opp)
        await db_session.commit()

        # Update status
        opp.status = "saved"
        await db_session.commit()
        await db_session.refresh(opp)

        assert opp.status == "saved"


class TestSetting:
    """Tests for Setting model."""

    @pytest.mark.asyncio
    async def test_create_setting(self, db_session):
        """Test creating a setting."""
        setting = Setting(key="test_setting", value={"enabled": True, "count": 10})
        db_session.add(setting)
        await db_session.commit()
        await db_session.refresh(setting)

        assert setting.key == "test_setting"
        assert setting.value["enabled"] is True
        assert setting.value["count"] == 10
