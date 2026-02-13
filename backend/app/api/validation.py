"""Validation API endpoints."""

from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Opportunity, ValidationExperiment, get_session
from app.validators.landing_generator import LandingPageGenerator
from app.validators.validation_scorer import ValidationScorer

router = APIRouter()


class ExperimentCreate(BaseModel):
    """Create validation experiment request."""

    experiment_type: Literal["landing_page", "survey", "waitlist"]
    hypothesis: str | None = Field(None, max_length=1000)
    target_metric: str | None = Field(None, max_length=100)
    template_type: Literal["problem_solution", "waitlist", "feature_vote"] | None = None


class ExperimentResponse(BaseModel):
    """Validation experiment response."""

    id: int
    opportunity_id: int
    experiment_type: str
    hypothesis: str | None
    target_metric: str | None
    status: str
    results: dict | None
    landing_page_url: str | None
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    completed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class RecordResults(BaseModel):
    """Record experiment results."""

    results: dict = Field(
        ..., description="Results data (e.g., signups, clicks, conversions)"
    )
    status: Literal["draft", "active", "completed"] | None = None


class ValidationScoreResponse(BaseModel):
    """Validation score response."""

    total_score: float
    specificity: float
    actionability: float
    testability: float
    recommended_experiments: list[dict[str, str]]


@router.post("/{opportunity_id}/experiments")
async def create_experiment(
    opportunity_id: int,
    experiment_data: ExperimentCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create a validation experiment for an opportunity.

    Args:
        opportunity_id: ID of the opportunity
        experiment_data: Experiment creation data
        session: Database session

    Returns:
        Created experiment data

    Raises:
        HTTPException: If opportunity not found
    """
    # Check if opportunity exists
    query = select(Opportunity).where(Opportunity.id == opportunity_id)
    result = await session.execute(query)
    opportunity = result.scalar_one_or_none()

    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    # Generate landing page HTML if it's a landing_page experiment
    landing_page_html = None
    if (
        experiment_data.experiment_type == "landing_page"
        and experiment_data.template_type
    ):
        landing_page_html = _generate_landing_page(
            opportunity, experiment_data.template_type
        )

    # Create experiment
    experiment = ValidationExperiment(
        opportunity_id=opportunity_id,
        experiment_type=experiment_data.experiment_type,
        hypothesis=experiment_data.hypothesis,
        target_metric=experiment_data.target_metric,
        status="draft",
        landing_page_html=landing_page_html,
    )

    session.add(experiment)
    await session.commit()
    await session.refresh(experiment)

    return ExperimentResponse.model_validate(experiment)


@router.get("/{opportunity_id}/experiments")
async def list_experiments(
    opportunity_id: int,
    status: str | None = Query(None, description="Filter by status"),
    session: AsyncSession = Depends(get_session),
):
    """List all validation experiments for an opportunity.

    Args:
        opportunity_id: ID of the opportunity
        status: Optional status filter
        session: Database session

    Returns:
        List of experiments

    Raises:
        HTTPException: If opportunity not found
    """
    # Check if opportunity exists
    opp_query = select(Opportunity).where(Opportunity.id == opportunity_id)
    opp_result = await session.execute(opp_query)
    opportunity = opp_result.scalar_one_or_none()

    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    # Get experiments
    query = select(ValidationExperiment).where(
        ValidationExperiment.opportunity_id == opportunity_id
    )

    if status:
        query = query.where(ValidationExperiment.status == status)

    query = query.order_by(ValidationExperiment.created_at.desc())

    result = await session.execute(query)
    experiments = result.scalars().all()

    return {
        "items": [ExperimentResponse.model_validate(exp) for exp in experiments],
        "total": len(experiments),
    }


@router.get("/{opportunity_id}/experiments/{experiment_id}")
async def get_experiment(
    opportunity_id: int,
    experiment_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get a specific validation experiment.

    Args:
        opportunity_id: ID of the opportunity
        experiment_id: ID of the experiment
        session: Database session

    Returns:
        Experiment data

    Raises:
        HTTPException: If experiment not found or doesn't belong to opportunity
    """
    query = select(ValidationExperiment).where(
        ValidationExperiment.id == experiment_id,
        ValidationExperiment.opportunity_id == opportunity_id,
    )
    result = await session.execute(query)
    experiment = result.scalar_one_or_none()

    if not experiment:
        raise HTTPException(
            status_code=404,
            detail="Experiment not found or doesn't belong to this opportunity",
        )

    return ExperimentResponse.model_validate(experiment)


@router.post("/{opportunity_id}/experiments/{experiment_id}/record")
async def record_results(
    opportunity_id: int,
    experiment_id: int,
    data: RecordResults,
    session: AsyncSession = Depends(get_session),
):
    """Record results for a validation experiment.

    Args:
        opportunity_id: ID of the opportunity
        experiment_id: ID of the experiment
        data: Results data
        session: Database session

    Returns:
        Updated experiment data

    Raises:
        HTTPException: If experiment not found
    """
    query = select(ValidationExperiment).where(
        ValidationExperiment.id == experiment_id,
        ValidationExperiment.opportunity_id == opportunity_id,
    )
    result = await session.execute(query)
    experiment = result.scalar_one_or_none()

    if not experiment:
        raise HTTPException(
            status_code=404,
            detail="Experiment not found or doesn't belong to this opportunity",
        )

    # Update results
    experiment.results = data.results
    experiment.updated_at = datetime.now(timezone.utc)

    # Update status if provided
    if data.status:
        experiment.status = data.status
        if data.status == "active" and not experiment.started_at:
            experiment.started_at = datetime.now(timezone.utc)
        elif data.status == "completed" and not experiment.completed_at:
            experiment.completed_at = datetime.now(timezone.utc)

    await session.commit()
    await session.refresh(experiment)

    return {
        "message": "Results recorded successfully",
        "experiment": ExperimentResponse.model_validate(experiment),
    }


@router.get("/{opportunity_id}/experiments/{experiment_id}/landing-page")
async def get_landing_page(
    opportunity_id: int,
    experiment_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get the generated landing page HTML for an experiment.

    Args:
        opportunity_id: ID of the opportunity
        experiment_id: ID of the experiment
        session: Database session

    Returns:
        Landing page HTML

    Raises:
        HTTPException: If experiment not found or has no landing page
    """
    query = select(ValidationExperiment).where(
        ValidationExperiment.id == experiment_id,
        ValidationExperiment.opportunity_id == opportunity_id,
    )
    result = await session.execute(query)
    experiment = result.scalar_one_or_none()

    if not experiment:
        raise HTTPException(
            status_code=404,
            detail="Experiment not found or doesn't belong to this opportunity",
        )

    if not experiment.landing_page_html:
        raise HTTPException(
            status_code=404,
            detail="No landing page generated for this experiment",
        )

    return {
        "html": experiment.landing_page_html,
        "experiment_id": experiment_id,
    }


@router.get("/{opportunity_id}/validation-score")
async def get_validation_score(
    opportunity_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Calculate validation score for an opportunity.

    Args:
        opportunity_id: ID of the opportunity
        session: Database session

    Returns:
        Validation score and recommended experiments

    Raises:
        HTTPException: If opportunity not found
    """
    query = select(Opportunity).where(Opportunity.id == opportunity_id)
    result = await session.execute(query)
    opportunity = result.scalar_one_or_none()

    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    # Calculate validation score
    score = ValidationScorer.score_opportunity(
        title=opportunity.title,
        summary=opportunity.summary,
        product_type=opportunity.product_type,
        sector=opportunity.sector,
        suggested_features=opportunity.suggested_features,
        competitors=opportunity.competitors,
    )

    return ValidationScoreResponse(**score)


def _generate_landing_page(
    opportunity: Opportunity,
    template_type: Literal["problem_solution", "waitlist", "feature_vote"],
) -> str:
    """Generate landing page HTML for an opportunity.

    Args:
        opportunity: Opportunity object
        template_type: Type of landing page template

    Returns:
        HTML string
    """
    if template_type == "problem_solution":
        # Extract problem and solution from summary
        summary = opportunity.summary or ""
        problem = summary[:200] if len(summary) > 200 else summary
        solution = opportunity.title

        # Get features from suggested_features
        features = []
        if opportunity.suggested_features:
            features = [
                f.get("feature", str(f)) if isinstance(f, dict) else str(f)
                for f in opportunity.suggested_features[:5]
            ]

        return LandingPageGenerator.generate_problem_solution(
            title=opportunity.title,
            problem=problem,
            solution=solution,
            features=features if features else None,
        )

    elif template_type == "waitlist":
        tagline = f"{opportunity.product_type or 'Product'} for {opportunity.sector or 'Your Needs'}"
        description = opportunity.summary or opportunity.title

        # Generate value props
        value_props = []
        if opportunity.suggested_features:
            value_props = [
                f.get("feature", str(f)) if isinstance(f, dict) else str(f)
                for f in opportunity.suggested_features[:4]
            ]

        return LandingPageGenerator.generate_waitlist(
            title=opportunity.title,
            tagline=tagline,
            description=description,
            value_props=value_props if value_props else None,
        )

    elif template_type == "feature_vote":
        description = opportunity.summary or "Help us prioritize what to build next"

        # Convert suggested_features to feature dicts
        features = []
        if opportunity.suggested_features:
            for f in opportunity.suggested_features[:6]:
                if isinstance(f, dict):
                    features.append(
                        {
                            "name": f.get("feature", "Feature"),
                            "description": f.get("description", ""),
                        }
                    )
                else:
                    features.append({"name": str(f), "description": ""})

        # If no features, create some defaults
        if not features:
            features = [
                {"name": "Core Feature", "description": "The main functionality"},
                {"name": "Advanced Features", "description": "Power user tools"},
            ]

        return LandingPageGenerator.generate_feature_vote(
            title=opportunity.title,
            description=description,
            features=features,
        )

    else:
        raise ValueError(f"Unknown template type: {template_type}")
