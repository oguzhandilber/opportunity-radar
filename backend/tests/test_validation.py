"""Tests for validation functionality."""

import pytest
from datetime import datetime

from app.database import Opportunity, RawPost, ValidationExperiment
from app.validators.landing_generator import LandingPageGenerator
from app.validators.validation_scorer import ValidationScorer


class TestLandingPageGenerator:
    """Tests for LandingPageGenerator."""

    def test_generate_problem_solution(self):
        """Test problem-solution landing page generation."""
        html = LandingPageGenerator.generate_problem_solution(
            title="TaskMaster Pro",
            problem="Managing tasks across multiple projects is chaotic",
            solution="A unified task management system",
            features=["Smart prioritization", "Team collaboration", "Time tracking"],
            cta_text="Get Early Access",
        )

        assert "TaskMaster Pro" in html
        assert "Managing tasks" in html
        assert "unified task management" in html
        assert "Smart prioritization" in html
        assert "Get Early Access" in html
        assert "<!DOCTYPE html>" in html

    def test_generate_problem_solution_minimal(self):
        """Test problem-solution page with minimal data."""
        html = LandingPageGenerator.generate_problem_solution(
            title="Simple Tool",
            problem="A problem",
            solution="A solution",
        )

        assert "Simple Tool" in html
        assert "A problem" in html
        assert "A solution" in html

    def test_generate_waitlist(self):
        """Test waitlist landing page generation."""
        html = LandingPageGenerator.generate_waitlist(
            title="InnovatePro",
            tagline="The future of productivity",
            description="A revolutionary tool for modern teams",
            value_props=["Fast", "Secure", "Easy to use"],
        )

        assert "InnovatePro" in html
        assert "future of productivity" in html
        assert "revolutionary tool" in html
        assert "Fast" in html
        assert "Secure" in html

    def test_generate_feature_vote(self):
        """Test feature voting landing page generation."""
        features = [
            {"name": "Dashboard", "description": "Visual overview of all tasks"},
            {"name": "API Access", "description": "Integrate with other tools"},
        ]
        html = LandingPageGenerator.generate_feature_vote(
            title="FeatureVote App",
            description="Help us prioritize features",
            features=features,
        )

        assert "FeatureVote App" in html
        assert "Dashboard" in html
        assert "Visual overview" in html
        assert "API Access" in html

    def test_generate_with_type(self):
        """Test generate method with template type."""
        html = LandingPageGenerator.generate(
            template_type="waitlist",
            title="Test App",
            tagline="Test tagline",
            description="Test description",
        )

        assert "Test App" in html
        assert "Test tagline" in html

    def test_generate_invalid_type(self):
        """Test generate method with invalid template type."""
        with pytest.raises(ValueError, match="Unknown template type"):
            LandingPageGenerator.generate(
                template_type="invalid_type",  # type: ignore
                title="Test",
            )


class TestValidationScorer:
    """Tests for ValidationScorer."""

    def test_score_opportunity_high_quality(self):
        """Test scoring a high-quality opportunity."""
        score = ValidationScorer.score_opportunity(
            title="AI-Powered Task Management Tool for Remote Teams",
            summary="A comprehensive project management solution that helps remote teams collaborate effectively with AI-powered insights and automated workflows.",
            product_type="SaaS",
            sector="Productivity",
            suggested_features=[
                {"feature": "AI task prioritization"},
                {"feature": "Team chat integration"},
                {"feature": "Automated reporting"},
                {"feature": "Time tracking"},
            ],
            competitors=[
                {"name": "Asana"},
                {"name": "Monday.com"},
            ],
        )

        assert score["total_score"] >= 7.0
        assert score["specificity"] >= 6.0
        assert score["actionability"] >= 6.0
        assert score["testability"] >= 5.0
        assert len(score["recommended_experiments"]) > 0

    def test_score_opportunity_minimal(self):
        """Test scoring a minimal opportunity."""
        score = ValidationScorer.score_opportunity(
            title="New App",
            summary=None,
            product_type=None,
            sector=None,
            suggested_features=None,
            competitors=None,
        )

        assert score["total_score"] < 5.0
        assert score["specificity"] < 5.0
        assert score["actionability"] < 5.0
        # Still has some testability
        assert score["testability"] >= 3.0

    def test_score_specificity(self):
        """Test specificity scoring."""
        score = ValidationScorer._score_specificity(
            title="CRM Platform for Small Business Sales Teams",
            summary="A customer relationship management tool designed specifically for small business sales teams with limited technical expertise.",
            product_type="SaaS",
            sector="Sales",
        )

        # Should score highly on specificity
        assert score >= 7.0

    def test_score_actionability(self):
        """Test actionability scoring."""
        score = ValidationScorer._score_actionability(
            suggested_features=[
                {"feature": "Feature 1"},
                {"feature": "Feature 2"},
                {"feature": "Feature 3"},
                {"feature": "Feature 4"},
                {"feature": "Feature 5"},
            ],
            competitors=[
                {"name": "Comp 1"},
                {"name": "Comp 2"},
                {"name": "Comp 3"},
            ],
        )

        # Should score highly with many features and competitors
        assert score >= 8.0

    def test_score_testability(self):
        """Test testability scoring."""
        score = ValidationScorer._score_testability(
            product_type="SaaS",
            summary="Users struggle with managing their customer data efficiently",
            suggested_features=[
                {"feature": "Feature 1"},
                {"feature": "Feature 2"},
                {"feature": "Feature 3"},
            ],
        )

        # Should score well for SaaS with problem and features
        assert score >= 7.0

    def test_recommend_experiments_high_score(self):
        """Test experiment recommendations for high-scoring opportunity."""
        experiments = ValidationScorer._recommend_experiments(
            total_score=8.5,
            specificity=8.0,
            actionability=9.0,
            testability=8.0,
            product_type="SaaS",
        )

        # Should recommend multiple experiments
        assert len(experiments) >= 2
        # Should include waitlist
        assert any(exp["type"] == "waitlist" for exp in experiments)
        # High actionability should include feature vote
        assert any(exp["type"] == "feature_vote" for exp in experiments)

    def test_recommend_experiments_low_score(self):
        """Test experiment recommendations for low-scoring opportunity."""
        experiments = ValidationScorer._recommend_experiments(
            total_score=4.0,
            specificity=3.0,
            actionability=4.0,
            testability=5.0,
            product_type=None,
        )

        # Should still recommend at least waitlist
        assert len(experiments) >= 1
        assert any(exp["type"] == "waitlist" for exp in experiments)


class TestValidationExperimentModel:
    """Tests for ValidationExperiment database model."""

    @pytest.mark.asyncio
    async def test_create_experiment(self, db_session):
        """Test creating a validation experiment."""
        # Create opportunity first
        post = RawPost(
            source="reddit",
            external_id="test123",
            content="Test post content",
        )
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
        await db_session.refresh(opp)

        # Create experiment
        experiment = ValidationExperiment(
            opportunity_id=opp.id,
            experiment_type="landing_page",
            hypothesis="Users will sign up for waitlist",
            target_metric="email_signups",
            status="draft",
            landing_page_html="<html>Test</html>",
        )
        db_session.add(experiment)
        await db_session.commit()
        await db_session.refresh(experiment)

        assert experiment.id is not None
        assert experiment.opportunity_id == opp.id
        assert experiment.experiment_type == "landing_page"
        assert experiment.status == "draft"

    @pytest.mark.asyncio
    async def test_experiment_relationship(self, db_session):
        """Test relationship between opportunity and experiments."""
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        # Create opportunity
        post = RawPost(
            source="hackernews",
            external_id="hn456",
            content="Show HN: My app",
        )
        db_session.add(post)
        await db_session.commit()
        await db_session.refresh(post)

        opp = Opportunity(
            raw_post_id=post.id,
            title="Test App",
            status="new",
        )
        db_session.add(opp)
        await db_session.commit()
        await db_session.refresh(opp)

        # Create multiple experiments
        exp1 = ValidationExperiment(
            opportunity_id=opp.id,
            experiment_type="waitlist",
            status="draft",
        )
        exp2 = ValidationExperiment(
            opportunity_id=opp.id,
            experiment_type="landing_page",
            status="active",
        )
        db_session.add(exp1)
        db_session.add(exp2)
        await db_session.commit()

        # Query with relationship loaded
        query = (
            select(Opportunity)
            .options(selectinload(Opportunity.validation_experiments))
            .where(Opportunity.id == opp.id)
        )
        result = await db_session.execute(query)
        loaded_opp = result.scalar_one()

        assert len(loaded_opp.validation_experiments) == 2

    @pytest.mark.asyncio
    async def test_update_experiment_results(self, db_session):
        """Test updating experiment results."""
        # Create opportunity and experiment
        post = RawPost(source="test", external_id="test789", content="Test")
        db_session.add(post)
        await db_session.commit()
        await db_session.refresh(post)

        opp = Opportunity(raw_post_id=post.id, title="Test", status="new")
        db_session.add(opp)
        await db_session.commit()
        await db_session.refresh(opp)

        experiment = ValidationExperiment(
            opportunity_id=opp.id,
            experiment_type="waitlist",
            status="draft",
        )
        db_session.add(experiment)
        await db_session.commit()
        await db_session.refresh(experiment)

        # Update results
        experiment.results = {"signups": 25, "clicks": 100}
        experiment.status = "active"
        experiment.started_at = datetime.utcnow()
        await db_session.commit()
        await db_session.refresh(experiment)

        assert experiment.results["signups"] == 25
        assert experiment.results["clicks"] == 100
        assert experiment.status == "active"
        assert experiment.started_at is not None

    @pytest.mark.asyncio
    async def test_cascade_delete(self, db_session):
        """Test that experiments are deleted when opportunity is deleted."""
        from sqlalchemy import select

        # Create opportunity and experiment
        post = RawPost(source="test", external_id="cascade_test", content="Test")
        db_session.add(post)
        await db_session.commit()
        await db_session.refresh(post)

        opp = Opportunity(raw_post_id=post.id, title="Test", status="new")
        db_session.add(opp)
        await db_session.commit()
        await db_session.refresh(opp)

        experiment = ValidationExperiment(
            opportunity_id=opp.id,
            experiment_type="waitlist",
            status="draft",
        )
        db_session.add(experiment)
        await db_session.commit()
        await db_session.refresh(experiment)

        experiment_id = experiment.id

        # Delete opportunity
        await db_session.delete(opp)
        await db_session.commit()

        # Check that experiment was also deleted
        query = select(ValidationExperiment).where(ValidationExperiment.id == experiment_id)
        result = await db_session.execute(query)
        deleted_experiment = result.scalar_one_or_none()

        assert deleted_experiment is None
