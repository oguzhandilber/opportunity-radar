"""Tests for validation tools functionality."""

import pytest
from datetime import datetime

from app.validators.toolkit import (
    ValidationToolkit,
    ValidationToolType,
    ValidationTool
)
from app.validators.simulator import ValidationSimulator
from app.validators.recommender import ValidationRecommender


class TestValidationToolkit:
    """Test validation toolkit."""

    def test_get_all_tools(self):
        """Test getting all validation tools."""
        toolkit = ValidationToolkit()
        tools = toolkit.get_all_tools()

        assert len(tools) > 0
        assert all(isinstance(tool, ValidationTool) for tool in tools)

        # Check specific tools exist
        tool_types = [tool.tool_type for tool in tools]
        assert ValidationToolType.LANDING_PAGE in tool_types
        assert ValidationToolType.AD_CAMPAIGN in tool_types
        assert ValidationToolType.MVP in tool_types

    def test_get_tool_by_type(self):
        """Test getting a specific tool by type."""
        toolkit = ValidationToolkit()
        tool = toolkit.get_tool(ValidationToolType.LANDING_PAGE)

        assert tool is not None
        assert tool.tool_type == ValidationToolType.LANDING_PAGE
        assert tool.name
        assert tool.description
        assert len(tool.setup_steps) > 0
        assert len(tool.expected_metrics) > 0

    def test_get_tools_by_difficulty(self):
        """Test filtering tools by difficulty."""
        toolkit = ValidationToolkit()
        easy_tools = toolkit.get_tools_by_difficulty("easy")

        assert len(easy_tools) > 0
        assert all(tool.difficulty == "easy" for tool in easy_tools)

    def test_get_tools_by_budget(self):
        """Test filtering tools by budget."""
        toolkit = ValidationToolkit()
        cheap_tools = toolkit.get_tools_by_budget(100)

        assert len(cheap_tools) > 0
        assert all(tool.cost_estimate_min <= 100 for tool in cheap_tools)

    def test_get_tools_by_timeframe(self):
        """Test filtering tools by timeframe."""
        toolkit = ValidationToolkit()
        quick_tools = toolkit.get_tools_by_timeframe(7)

        assert len(quick_tools) > 0
        assert all(tool.time_estimate_days <= 7 for tool in quick_tools)


class TestValidationSimulator:
    """Test validation simulator."""

    def test_simulate_landing_page_high_quality(self):
        """Test landing page simulation with high quality opportunity."""
        simulator = ValidationSimulator()
        result = simulator.simulate_landing_page(
            payment_intent=0.8,
            success_prediction=75,
            niche_fit=8,
            traffic_volume=1000
        )

        assert result.tool_type == ValidationToolType.LANDING_PAGE
        assert "visitors" in result.metrics
        assert "signups" in result.metrics
        assert "conversion_rate" in result.metrics
        assert result.metrics["visitors"] == 1000
        assert result.metrics["signups"] > 0
        assert result.metrics["conversion_rate"] > 0
        assert result.confidence > 0
        assert len(result.assumptions) > 0

    def test_simulate_landing_page_low_quality(self):
        """Test landing page simulation with low quality opportunity."""
        simulator = ValidationSimulator()
        result = simulator.simulate_landing_page(
            payment_intent=0.2,
            success_prediction=30,
            niche_fit=3,
            traffic_volume=1000
        )

        # Low quality should result in lower conversion
        assert result.metrics["conversion_rate"] < 3  # Less than 3%

    def test_simulate_ad_campaign(self):
        """Test ad campaign simulation."""
        simulator = ValidationSimulator()
        result = simulator.simulate_ad_campaign(
            payment_intent=0.6,
            success_prediction=60,
            budget=500,
            platform="google"
        )

        assert result.tool_type == ValidationToolType.AD_CAMPAIGN
        assert "impressions" in result.metrics
        assert "clicks" in result.metrics
        assert "ctr" in result.metrics
        assert "cpc" in result.metrics
        assert "conversions" in result.metrics
        assert result.metrics["budget_spent"] == 500
        assert result.metrics["clicks"] > 0

    def test_simulate_email_list(self):
        """Test email list simulation."""
        simulator = ValidationSimulator()
        result = simulator.simulate_email_list(
            payment_intent=0.7,
            success_prediction=65,
            promotion_reach=5000
        )

        assert result.tool_type == ValidationToolType.EMAIL_LIST
        assert "subscribers" in result.metrics
        assert "signup_rate" in result.metrics
        assert "est_open_rate" in result.metrics
        assert result.metrics["reach"] == 5000
        assert result.metrics["subscribers"] > 0

    def test_simulate_survey(self):
        """Test survey simulation."""
        simulator = ValidationSimulator()
        result = simulator.simulate_survey(
            payment_intent=0.5,
            target_responses=100,
            distribution_size=500
        )

        assert result.tool_type == ValidationToolType.SURVEY
        assert "responses" in result.metrics
        assert "response_rate" in result.metrics
        assert "willingness_to_pay_pct" in result.metrics
        assert result.metrics["distributed"] == 500

    def test_simulate_mvp(self):
        """Test MVP simulation."""
        simulator = ValidationSimulator()
        result = simulator.simulate_mvp(
            payment_intent=0.8,
            success_prediction=70,
            niche_fit=7,
            initial_users=100
        )

        assert result.tool_type == ValidationToolType.MVP
        assert "day1_retention" in result.metrics
        assert "day7_retention" in result.metrics
        assert "day30_retention" in result.metrics
        assert "conversion_to_paid" in result.metrics
        assert result.metrics["initial_users"] == 100

    def test_simulate_generic(self):
        """Test generic simulate method."""
        simulator = ValidationSimulator()
        result = simulator.simulate(
            tool_type=ValidationToolType.LANDING_PAGE,
            payment_intent=0.6,
            success_prediction=60,
            niche_fit=6
        )

        assert result.tool_type == ValidationToolType.LANDING_PAGE
        assert result.metrics


class TestValidationRecommender:
    """Test validation recommender."""

    def test_recommend_low_budget(self):
        """Test recommendation with low budget."""
        recommender = ValidationRecommender()
        plan = recommender.recommend(
            budget="low",
            time_available="short",
            risk_tolerance="low"
        )

        assert plan is not None
        assert len(plan.steps) > 0
        # Low budget tools should start under $300, but max might be higher
        assert plan.total_cost_min <= 300  # Minimum cost should be low
        assert plan.confidence_level in ["low", "medium", "high"]
        assert plan.overall_strategy

        # Check that all steps can start within budget
        for step in plan.steps:
            assert step.tool.cost_estimate_min <= 300

    def test_recommend_high_budget(self):
        """Test recommendation with high budget."""
        recommender = ValidationRecommender()
        plan = recommender.recommend(
            budget="high",
            time_available="long",
            risk_tolerance="high"
        )

        assert len(plan.steps) > 0
        # High budget/risk might include MVP
        tool_types = [step.tool.tool_type for step in plan.steps]
        # With high budget and risk, might see more expensive tools

    def test_recommend_with_high_payment_intent(self):
        """Test recommendation with high payment intent."""
        recommender = ValidationRecommender()
        plan = recommender.recommend(
            budget="medium",
            time_available="medium",
            risk_tolerance="medium",
            payment_intent=0.9,
            success_prediction=80
        )

        # High payment intent should favor paid validation
        tool_types = [step.tool.tool_type for step in plan.steps]
        # Might include ad campaign or landing page

        assert len(plan.steps) > 0

    def test_recommend_with_low_payment_intent(self):
        """Test recommendation with low payment intent."""
        recommender = ValidationRecommender()
        plan = recommender.recommend(
            budget="low",
            time_available="short",
            risk_tolerance="low",
            payment_intent=0.2,
            success_prediction=30
        )

        # Low payment intent should favor cheap validation
        for step in plan.steps:
            assert step.tool.difficulty in ["easy", "medium"]

    def test_recommend_b2b_product(self):
        """Test recommendation for B2B product."""
        recommender = ValidationRecommender()
        plan = recommender.recommend(
            budget="medium",
            time_available="medium",
            risk_tolerance="medium",
            product_type="B2B SaaS"
        )

        assert len(plan.steps) > 0
        # B2B might favor cold outreach or landing pages

    def test_validation_step_attributes(self):
        """Test that validation steps have all required attributes."""
        recommender = ValidationRecommender()
        plan = recommender.recommend(
            budget="medium",
            time_available="medium",
            risk_tolerance="medium"
        )

        for step in plan.steps:
            assert step.priority > 0
            assert step.reasoning
            assert step.expected_outcome
            assert step.risk_mitigation
            assert step.tool


@pytest.mark.asyncio
async def test_list_validation_tools_api(client):
    """Test listing validation tools via API."""
    response = await client.get("/api/validation-tools/tools")
    assert response.status_code == 200

    data = response.json()
    assert "tools" in data
    assert "total" in data
    assert data["total"] > 0
    assert len(data["tools"]) > 0

    # Check tool structure
    tool = data["tools"][0]
    assert "tool_type" in tool
    assert "name" in tool
    assert "description" in tool
    assert "setup_steps" in tool
    assert "expected_metrics" in tool
    assert "cost_estimate_min" in tool
    assert "cost_estimate_max" in tool


@pytest.mark.asyncio
async def test_get_specific_tool_api(client):
    """Test getting a specific tool via API."""
    response = await client.get("/api/validation-tools/tools/landing_page")
    assert response.status_code == 200

    data = response.json()
    assert data["tool_type"] == "landing_page"
    assert data["name"]
    assert len(data["setup_steps"]) > 0


@pytest.mark.asyncio
async def test_get_invalid_tool_api(client):
    """Test getting an invalid tool via API."""
    response = await client.get("/api/validation-tools/tools/invalid_tool")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_validation_tracker(client, db_session):
    """Test creating a validation tracker."""
    from app.database import Opportunity, RawPost

    # Create test opportunity
    raw_post = RawPost(
        source="reddit",
        external_id="test_123",
        content="Test post",
        author="test_user",
        url="https://reddit.com/test"
    )
    db_session.add(raw_post)
    await db_session.flush()

    opportunity = Opportunity(
        raw_post_id=raw_post.id,
        title="Test Opportunity",
        summary="Test summary",
        total_score=7.5
    )
    db_session.add(opportunity)
    await db_session.commit()
    await db_session.refresh(opportunity)

    # Create validation tracker
    response = await client.post(
        f"/api/validation-tools/opportunities/{opportunity.id}/validation",
        json={
            "tool_type": "landing_page",
            "config": {"traffic_volume": 1000},
            "notes": "Test validation"
        }
    )
    assert response.status_code == 200

    data = response.json()
    assert data["message"] == "Validation tracker created"
    assert "id" in data
    assert data["tracker"]["tool_type"] == "landing_page"
    assert data["tracker"]["status"] == "planned"


@pytest.mark.asyncio
async def test_list_validation_trackers(client, db_session):
    """Test listing validation trackers for an opportunity."""
    from app.database import Opportunity, RawPost, ValidationTracker

    # Create test opportunity
    raw_post = RawPost(
        source="reddit",
        external_id="test_456",
        content="Test post",
        author="test_user"
    )
    db_session.add(raw_post)
    await db_session.flush()

    opportunity = Opportunity(
        raw_post_id=raw_post.id,
        title="Test Opportunity",
        total_score=7.5
    )
    db_session.add(opportunity)
    await db_session.flush()

    # Create validation trackers
    tracker1 = ValidationTracker(
        opportunity_id=opportunity.id,
        tool_type="landing_page",
        status="planned"
    )
    tracker2 = ValidationTracker(
        opportunity_id=opportunity.id,
        tool_type="survey",
        status="completed"
    )
    db_session.add(tracker1)
    db_session.add(tracker2)
    await db_session.commit()

    # List trackers
    response = await client.get(f"/api/validation-tools/opportunities/{opportunity.id}/validation")
    assert response.status_code == 200

    data = response.json()
    assert "trackers" in data
    assert data["total"] == 2
    assert len(data["trackers"]) == 2


@pytest.mark.asyncio
async def test_simulate_validation_for_opportunity(client, db_session):
    """Test simulating validation for an opportunity."""
    from app.database import Opportunity, RawPost

    # Create test opportunity
    raw_post = RawPost(
        source="reddit",
        external_id="test_789",
        content="Test post"
    )
    db_session.add(raw_post)
    await db_session.flush()

    opportunity = Opportunity(
        raw_post_id=raw_post.id,
        title="Test Opportunity",
        payment_signal_strength=0.7,
        success_prediction=70,
        niche_fit_score=7.0,
        total_score=7.5
    )
    db_session.add(opportunity)
    await db_session.commit()
    await db_session.refresh(opportunity)

    # Simulate validation
    response = await client.post(
        f"/api/validation-tools/opportunities/{opportunity.id}/validation/simulate",
        json={
            "tool_type": "landing_page",
            "config": {"traffic_volume": 1000}
        }
    )
    assert response.status_code == 200

    data = response.json()
    assert data["tool_type"] == "landing_page"
    assert "metrics" in data
    assert "confidence" in data
    assert "assumptions" in data


@pytest.mark.asyncio
async def test_recommend_validation_plan(client, db_session):
    """Test getting validation plan recommendation."""
    from app.database import Opportunity, RawPost

    # Create test opportunity
    raw_post = RawPost(
        source="reddit",
        external_id="test_rec",
        content="Test post"
    )
    db_session.add(raw_post)
    await db_session.flush()

    opportunity = Opportunity(
        raw_post_id=raw_post.id,
        title="Test Opportunity",
        payment_signal_strength=0.6,
        success_prediction=60,
        product_type="SaaS",
        total_score=7.5
    )
    db_session.add(opportunity)
    await db_session.commit()
    await db_session.refresh(opportunity)

    # Get recommendation
    response = await client.post(
        f"/api/validation-tools/opportunities/{opportunity.id}/validation/recommend",
        json={
            "budget": "medium",
            "time_available": "medium",
            "risk_tolerance": "medium"
        }
    )
    assert response.status_code == 200

    data = response.json()
    assert "plan" in data
    assert "steps" in data["plan"]
    assert len(data["plan"]["steps"]) > 0
    assert "total_cost_min" in data["plan"]
    assert "total_cost_max" in data["plan"]
    assert "overall_strategy" in data["plan"]
    assert "confidence_level" in data["plan"]


@pytest.mark.asyncio
async def test_update_validation_tracker(client, db_session):
    """Test updating a validation tracker."""
    from app.database import Opportunity, RawPost, ValidationTracker

    # Create test opportunity
    raw_post = RawPost(
        source="reddit",
        external_id="test_upd",
        content="Test post"
    )
    db_session.add(raw_post)
    await db_session.flush()

    opportunity = Opportunity(
        raw_post_id=raw_post.id,
        title="Test Opportunity",
        total_score=7.5
    )
    db_session.add(opportunity)
    await db_session.flush()

    tracker = ValidationTracker(
        opportunity_id=opportunity.id,
        tool_type="landing_page",
        status="planned"
    )
    db_session.add(tracker)
    await db_session.commit()
    await db_session.refresh(tracker)

    # Update tracker
    response = await client.patch(
        f"/api/validation-tools/validation/{tracker.id}",
        json={
            "status": "completed",
            "results": {"signups": 50, "conversion_rate": 2.5}
        }
    )
    assert response.status_code == 200

    data = response.json()
    assert data["tracker"]["status"] == "completed"
    assert data["tracker"]["results"]["signups"] == 50
    assert data["tracker"]["is_simulated"] is False


@pytest.mark.asyncio
async def test_simulate_tracker_validation(client, db_session):
    """Test running simulation on an existing tracker."""
    from app.database import Opportunity, RawPost, ValidationTracker

    # Create test opportunity
    raw_post = RawPost(
        source="reddit",
        external_id="test_sim",
        content="Test post"
    )
    db_session.add(raw_post)
    await db_session.flush()

    opportunity = Opportunity(
        raw_post_id=raw_post.id,
        title="Test Opportunity",
        payment_signal_strength=0.7,
        success_prediction=70,
        niche_fit_score=7.0,
        total_score=7.5
    )
    db_session.add(opportunity)
    await db_session.flush()

    tracker = ValidationTracker(
        opportunity_id=opportunity.id,
        tool_type="landing_page",
        status="planned",
        config={"traffic_volume": 1000}
    )
    db_session.add(tracker)
    await db_session.commit()
    await db_session.refresh(tracker)

    # Simulate
    response = await client.post(f"/api/validation-tools/validation/{tracker.id}/simulate")
    assert response.status_code == 200

    data = response.json()
    assert "tracker" in data
    assert "simulation" in data
    assert data["tracker"]["simulated_results"] is not None
    assert data["tracker"]["is_simulated"] is True
