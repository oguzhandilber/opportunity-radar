"""Comprehensive tests for new SaaS features."""

import pytest
import asyncio
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session, User, Workspace, Alert, SavedSearch, Subscription
from app.auth.password_manager import password_manager
from app.auth.jwt_handler import JWTHandler


class TestPostgreSQLMigration:
    """Test PostgreSQL migration and database functionality."""

    @pytest.mark.asyncio
    async def test_postgres_connection(self, client: AsyncClient):
        """Test PostgreSQL connection via health endpoint."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_user_model_exists(self, session: AsyncSession):
        """Test User model was created properly."""
        # Create test user
        user = User(
            email="test@example.com",
            password_hash=password_manager.hash_password("TestPassword123!"),
            first_name="Test",
            last_name="User",
            is_verified=True,
        )
        session.add(user)
        await session.commit()

        # Verify user exists
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.first_name == "Test"


class TestAuthentication:
    """Test JWT authentication system."""

    @pytest.mark.asyncio
    async def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "TestPassword123!"
        hashed = password_manager.hash_password(password)

        assert password != hashed
        assert password_manager.verify_password(password, hashed)
        assert not password_manager.verify_password("WrongPassword", hashed)

    @pytest.mark.asyncio
    async def test_jwt_token_generation(self):
        """Test JWT token generation and validation."""
        jwt_handler = JWTHandler()

        user_data = {"user_id": 1, "email": "test@example.com", "role": "owner"}

        tokens = jwt_handler.generate_tokens(user_data)

        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"
        assert tokens["expires_in"] > 0

        # Verify token
        payload = jwt_handler.verify_token(tokens["access_token"])
        assert payload is not None
        assert payload["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_user_registration(self, client: AsyncClient):
        """Test user registration endpoint."""
        user_data = {
            "email": "newuser@example.com",
            "password": "TestPassword123!",
            "first_name": "New",
            "last_name": "User",
        }

        response = await client.post("/api/auth/register", json=user_data)
        assert response.status_code == 200

        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["first_name"] == user_data["first_name"]
        assert "id" in data

    @pytest.mark.asyncio
    async def test_user_login(self, client: AsyncClient):
        """Test user login and token generation."""
        # First register a user
        user_data = {
            "email": "loginuser@example.com",
            "password": "TestPassword123!",
            "first_name": "Login",
            "last_name": "User",
        }
        await client.post("/api/auth/register", json=user_data)

        # Then login
        login_data = {"username": user_data["email"], "password": user_data["password"]}

        response = await client.post("/api/auth/login", data=login_data)
        assert response.status_code == 200

        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_protected_route_access(self, client: AsyncClient):
        """Test accessing protected routes with valid token."""
        # Register and login to get token
        user_data = {
            "email": "protected@example.com",
            "password": "TestPassword123!",
            "first_name": "Protected",
            "last_name": "User",
        }
        await client.post("/api/auth/register", json=user_data)

        login_data = {"username": user_data["email"], "password": user_data["password"]}
        login_response = await client.post("/api/auth/login", data=login_data)
        token = login_response.json()["access_token"]

        # Access protected route
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get("/api/alerts", headers=headers)

        assert response.status_code == 200


class TestAlerts:
    """Test alert/notification system."""

    @pytest.mark.asyncio
    async def test_create_alert(self, client: AsyncClient, auth_headers: dict):
        """Test creating a new alert."""
        alert_data = {
            "name": "High Score Opportunities",
            "conditions": {
                "min_total_score": 7.5,
                "sectors": ["SaaS", "Fintech"],
                "keywords": ["AI", "automation"],
            },
            "email_enabled": True,
        }

        response = await client.post(
            "/api/alerts", json=alert_data, headers=auth_headers
        )
        assert response.status_code == 201

        data = response.json()
        assert data["name"] == alert_data["name"]
        assert data["min_total_score"] == alert_data["conditions"]["min_total_score"]
        assert data["email_enabled"] is True

    @pytest.mark.asyncio
    async def test_list_alerts(self, client: AsyncClient, auth_headers: dict):
        """Test listing all alerts."""
        # Create an alert first
        alert_data = {
            "name": "Test Alert",
            "conditions": {"min_total_score": 6.0},
            "email_enabled": True,
        }
        await client.post("/api/alerts", json=alert_data, headers=auth_headers)

        # List alerts
        response = await client.get("/api/alerts", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    @pytest.mark.asyncio
    async def test_alert_limit_enforcement(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that alert limits are enforced based on subscription tier."""
        # Create maximum allowed alerts for free tier (3)
        for i in range(3):
            alert_data = {
                "name": f"Test Alert {i}",
                "conditions": {"min_total_score": 6.0},
                "email_enabled": True,
            }
            response = await client.post(
                "/api/alerts", json=alert_data, headers=auth_headers
            )
            assert response.status_code == 201

        # Try to create 4th alert (should fail for free tier)
        alert_data = {
            "name": "Fourth Alert",
            "conditions": {"min_total_score": 6.0},
            "email_enabled": True,
        }
        response = await client.post(
            "/api/alerts", json=alert_data, headers=auth_headers
        )
        assert response.status_code == 403


class TestSavedSearches:
    """Test saved searches functionality."""

    @pytest.mark.asyncio
    async def test_create_saved_search(self, client: AsyncClient, auth_headers: dict):
        """Test creating a saved search."""
        search_data = {
            "name": "SaaS Opportunities",
            "criteria": {"sectors": ["SaaS"], "min_score": 7.0, "keywords": ["B2B"]},
        }

        response = await client.post(
            "/api/saved-searches", json=search_data, headers=auth_headers
        )
        assert response.status_code == 201

        data = response.json()
        assert data["name"] == search_data["name"]
        assert data["sectors"] == search_data["criteria"]["sectors"]
        assert data["min_score"] == search_data["criteria"]["min_score"]

    @pytest.mark.asyncio
    async def test_list_saved_searches(self, client: AsyncClient, auth_headers: dict):
        """Test listing saved searches."""
        # Create a saved search
        search_data = {"name": "Test Search", "criteria": {"sectors": ["Fintech"]}}
        await client.post("/api/saved-searches", json=search_data, headers=auth_headers)

        # List saved searches
        response = await client.get("/api/saved-searches", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    @pytest.mark.asyncio
    async def test_saved_search_limits(self, client: AsyncClient, auth_headers: dict):
        """Test that saved search limits are enforced."""
        # Create maximum allowed saved searches for free tier (5)
        for i in range(5):
            search_data = {
                "name": f"Test Search {i}",
                "criteria": {"sectors": ["SaaS"]},
            }
            response = await client.post(
                "/api/saved-searches", json=search_data, headers=auth_headers
            )
            assert response.status_code == 201

        # Try to create 6th saved search (should fail for free tier)
        search_data = {"name": "Sixth Search", "criteria": {"sectors": ["SaaS"]}}
        response = await client.post(
            "/api/saved-searches", json=search_data, headers=auth_headers
        )
        assert response.status_code == 403


class TestSubscriptions:
    """Test subscription tier enforcement."""

    @pytest.mark.asyncio
    async def test_subscription_model(self, session: AsyncSession):
        """Test subscription model creation."""
        # Create test user and workspace
        user = User(
            email="subuser@example.com",
            password_hash=password_manager.hash_password("TestPass123!"),
            first_name="Sub",
            last_name="User",
        )
        session.add(user)
        await session.flush()

        workspace = Workspace(
            name="Test Workspace", slug="test-workspace", created_by=user.id
        )
        session.add(workspace)
        await session.flush()

        # Create subscription
        subscription = Subscription(
            user_id=user.id, workspace_id=workspace.id, plan="free", status="active"
        )
        session.add(subscription)
        await session.commit()

        assert subscription.id is not None
        assert subscription.plan == "free"
        assert subscription.status == "active"


# Fixtures for tests
@pytest.fixture
async def auth_headers(client: AsyncClient):
    """Create a test user and return auth headers."""
    # Register user
    user_data = {
        "email": "testfixture@example.com",
        "password": "TestPassword123!",
        "first_name": "Test",
        "last_name": "Fixture",
    }
    await client.post("/api/auth/register", json=user_data)

    # Login to get token
    login_data = {"username": user_data["email"], "password": user_data["password"]}
    response = await client.post("/api/auth/login", data=login_data)
    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def client():
    """Create test client."""
    from httpx import AsyncClient
    from app.main import app

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def session():
    """Create database session for tests."""
    from app.database import get_session

    async for session in get_session():
        yield session
