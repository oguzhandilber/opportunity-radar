"""Tests for UserProfile model."""

import pytest
from datetime import datetime

from app.models.app_store import UserProfile


class TestUserProfile:
    """Tests for UserProfile model."""

    @pytest.mark.asyncio
    async def test_create_user_profile(self, db_session):
        """Test creating a user profile."""
        profile = UserProfile(
            email="test@example.com",
            phone_number="+1234567890",
        )
        db_session.add(profile)
        await db_session.commit()
        await db_session.refresh(profile)

        assert profile.id is not None
        assert profile.email == "test@example.com"
        assert profile.phone_number == "+1234567890"
        assert profile.created_at is not None
        assert profile.updated_at is not None

    @pytest.mark.asyncio
    async def test_user_profile_email_unique(self, db_session):
        """Test email unique constraint."""
        from sqlalchemy.exc import IntegrityError

        profile1 = UserProfile(
            email="unique@example.com",
            phone_number="+1234567890",
        )
        db_session.add(profile1)
        await db_session.commit()

        profile2 = UserProfile(
            email="unique@example.com",
            phone_number="+0987654321",
        )
        db_session.add(profile2)

        with pytest.raises(IntegrityError):
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_user_profile_phone_optional(self, db_session):
        """Test that phone number is optional."""
        profile = UserProfile(
            email="nophone@example.com",
        )
        db_session.add(profile)
        await db_session.commit()
        await db_session.refresh(profile)

        assert profile.id is not None
        assert profile.email == "nophone@example.com"
        assert profile.phone_number is None

    @pytest.mark.asyncio
    async def test_user_profile_timestamps(self, db_session):
        """Test that timestamps are automatically set."""
        before = datetime.utcnow()
        profile = UserProfile(
            email="timestamp@example.com",
            phone_number="+1234567890",
        )
        db_session.add(profile)
        await db_session.commit()
        await db_session.refresh(profile)
        after = datetime.utcnow()

        assert profile.created_at is not None
        assert profile.updated_at is not None
        assert profile.created_at >= before
        assert profile.created_at <= after
