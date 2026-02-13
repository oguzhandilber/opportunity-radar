"""Validation tools API endpoints."""

from datetime import datetime, timezone
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import Opportunity, ValidationTracker, get_session
from app.validators.toolkit import ValidationToolkit, ValidationToolType
from app.validators.simulator import ValidationSimulator
from app.validators.recommender import ValidationRecommender


router = APIRouter()


class ValidationToolResponse(BaseModel):
    """Validation tool response model."""

    tool_type: str
    name: str
    description: str
    setup_steps: list[str]
    expected_metrics: list[str]
    cost_estimate_min: float
    cost_estimate_max: float
    time_estimate_days: int
    difficulty: str
    best_for: list[str]


class ValidationTrackerCreate(BaseModel):
    """Create validation tracker request."""

    tool_type: str = Field(..., description="Type of validation tool")
    config: dict = Field(
        default_factory=dict, description="Tool-specific configuration"
    )
    notes: Optional[str] = Field(None, max_length=5000)


class ValidationTrackerUpdate(BaseModel):
    """Update validation tracker request."""

    status: Optional[Literal["planned", "in_progress", "completed", "failed"]] = None
    results: Optional[dict] = None
    notes: Optional[str] = Field(None, max_length=5000)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ValidationTrackerResponse(BaseModel):
    """Validation tracker response model."""

    id: int
    opportunity_id: int
    tool_type: str
    status: str
    config: dict | None
    results: dict | None
    simulated_results: dict | None
    is_simulated: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    completed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class SimulateValidationRequest(BaseModel):
    """Simulate validation request."""

    tool_type: str
    config: dict = Field(default_factory=dict)


class RecommendationRequest(BaseModel):
    """Validation recommendation request."""

    budget: Literal["low", "medium", "high"] = "medium"
    time_available: Literal["short", "medium", "long"] = "medium"
    risk_tolerance: Literal["low", "medium", "high"] = "medium"


@router.get("/tools")
async def list_validation_tools():
    """List all available validation tools."""
    toolkit = ValidationToolkit()
    tools = toolkit.get_all_tools()

    return {
        "tools": [
            ValidationToolResponse(
                tool_type=tool.tool_type.value,
                name=tool.name,
                description=tool.description,
                setup_steps=tool.setup_steps,
                expected_metrics=tool.expected_metrics,
                cost_estimate_min=tool.cost_estimate_min,
                cost_estimate_max=tool.cost_estimate_max,
                time_estimate_days=tool.time_estimate_days,
                difficulty=tool.difficulty,
                best_for=tool.best_for,
            )
            for tool in tools
        ],
        "total": len(tools),
    }


@router.get("/tools/{tool_type}")
async def get_validation_tool(tool_type: str):
    """Get details for a specific validation tool."""
    try:
        tool_enum = ValidationToolType(tool_type)
    except ValueError:
        raise HTTPException(status_code=404, detail="Validation tool not found")

    toolkit = ValidationToolkit()
    tool = toolkit.get_tool(tool_enum)

    if not tool:
        raise HTTPException(status_code=404, detail="Validation tool not found")

    return ValidationToolResponse(
        tool_type=tool.tool_type.value,
        name=tool.name,
        description=tool.description,
        setup_steps=tool.setup_steps,
        expected_metrics=tool.expected_metrics,
        cost_estimate_min=tool.cost_estimate_min,
        cost_estimate_max=tool.cost_estimate_max,
        time_estimate_days=tool.time_estimate_days,
        difficulty=tool.difficulty,
        best_for=tool.best_for,
    )


@router.post("/opportunities/{opportunity_id}/validation")
async def create_validation_tracker(
    opportunity_id: int,
    request: ValidationTrackerCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create a new validation tracker for an opportunity."""
    # Check if opportunity exists
    query = select(Opportunity).where(Opportunity.id == opportunity_id)
    result = await session.execute(query)
    opportunity = result.scalar_one_or_none()

    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    # Validate tool type
    try:
        ValidationToolType(request.tool_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid tool type")

    # Create tracker
    tracker = ValidationTracker(
        opportunity_id=opportunity_id,
        tool_type=request.tool_type,
        config=request.config,
        notes=request.notes,
        status="planned",
    )

    session.add(tracker)
    await session.commit()
    await session.refresh(tracker)

    return {
        "message": "Validation tracker created",
        "id": tracker.id,
        "tracker": ValidationTrackerResponse.model_validate(tracker),
    }


@router.get("/opportunities/{opportunity_id}/validation")
async def list_validation_trackers(
    opportunity_id: int, session: AsyncSession = Depends(get_session)
):
    """Get all validation trackers for an opportunity."""
    # Check if opportunity exists
    query = select(Opportunity).where(Opportunity.id == opportunity_id)
    result = await session.execute(query)
    opportunity = result.scalar_one_or_none()

    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    # Get trackers
    query = (
        select(ValidationTracker)
        .where(ValidationTracker.opportunity_id == opportunity_id)
        .order_by(ValidationTracker.created_at.desc())
    )
    result = await session.execute(query)
    trackers = result.scalars().all()

    return {
        "trackers": [
            ValidationTrackerResponse.model_validate(tracker) for tracker in trackers
        ],
        "total": len(trackers),
    }


@router.get("/validation/{tracker_id}")
async def get_validation_tracker(
    tracker_id: int, session: AsyncSession = Depends(get_session)
):
    """Get a specific validation tracker."""
    query = select(ValidationTracker).where(ValidationTracker.id == tracker_id)
    result = await session.execute(query)
    tracker = result.scalar_one_or_none()

    if not tracker:
        raise HTTPException(status_code=404, detail="Validation tracker not found")

    return ValidationTrackerResponse.model_validate(tracker)


@router.patch("/validation/{tracker_id}")
async def update_validation_tracker(
    tracker_id: int,
    update: ValidationTrackerUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Update a validation tracker."""
    query = select(ValidationTracker).where(ValidationTracker.id == tracker_id)
    result = await session.execute(query)
    tracker = result.scalar_one_or_none()

    if not tracker:
        raise HTTPException(status_code=404, detail="Validation tracker not found")

    # Update fields
    if update.status is not None:
        tracker.status = update.status
    if update.results is not None:
        tracker.results = update.results
        tracker.is_simulated = 0  # Real results
    if update.notes is not None:
        tracker.notes = update.notes
    if update.started_at is not None:
        tracker.started_at = update.started_at
    if update.completed_at is not None:
        tracker.completed_at = update.completed_at

    tracker.updated_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(tracker)

    return {
        "message": "Validation tracker updated",
        "id": tracker_id,
        "tracker": ValidationTrackerResponse.model_validate(tracker),
    }


@router.post("/opportunities/{opportunity_id}/validation/simulate")
async def simulate_validation(
    opportunity_id: int,
    request: SimulateValidationRequest,
    session: AsyncSession = Depends(get_session),
):
    """Simulate validation results for an opportunity."""
    # Get opportunity
    query = select(Opportunity).where(Opportunity.id == opportunity_id)
    result = await session.execute(query)
    opportunity = result.scalar_one_or_none()

    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    # Validate tool type
    try:
        tool_type = ValidationToolType(request.tool_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid tool type")

    # Run simulation
    simulator = ValidationSimulator()
    simulation = simulator.simulate(
        tool_type=tool_type,
        payment_intent=opportunity.payment_signal_strength,
        success_prediction=opportunity.success_prediction,
        niche_fit=opportunity.niche_fit_score,
        config=request.config,
    )

    return {
        "tool_type": simulation.tool_type.value,
        "metrics": simulation.metrics,
        "confidence": simulation.confidence,
        "assumptions": simulation.assumptions,
        "notes": simulation.notes,
    }


@router.post("/validation/{tracker_id}/simulate")
async def simulate_tracker_validation(
    tracker_id: int, session: AsyncSession = Depends(get_session)
):
    """Run simulation for an existing validation tracker."""
    # Get tracker with opportunity
    query = (
        select(ValidationTracker)
        .options(selectinload(ValidationTracker.opportunity))
        .where(ValidationTracker.id == tracker_id)
    )
    result = await session.execute(query)
    tracker = result.scalar_one_or_none()

    if not tracker:
        raise HTTPException(status_code=404, detail="Validation tracker not found")

    opportunity = tracker.opportunity

    # Validate tool type
    try:
        tool_type = ValidationToolType(tracker.tool_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid tool type")

    # Run simulation
    simulator = ValidationSimulator()
    simulation = simulator.simulate(
        tool_type=tool_type,
        payment_intent=opportunity.payment_signal_strength,
        success_prediction=opportunity.success_prediction,
        niche_fit=opportunity.niche_fit_score,
        config=tracker.config or {},
    )

    # Update tracker with simulated results
    tracker.simulated_results = simulation.metrics
    tracker.is_simulated = 1
    tracker.updated_at = datetime.now(timezone.utc)

    await session.commit()
    await session.refresh(tracker)

    return {
        "message": "Simulation completed",
        "tracker": ValidationTrackerResponse.model_validate(tracker),
        "simulation": {
            "tool_type": simulation.tool_type.value,
            "metrics": simulation.metrics,
            "confidence": simulation.confidence,
            "assumptions": simulation.assumptions,
            "notes": simulation.notes,
        },
    }


@router.post("/opportunities/{opportunity_id}/validation/recommend")
async def recommend_validation_plan(
    opportunity_id: int,
    request: RecommendationRequest,
    session: AsyncSession = Depends(get_session),
):
    """Get recommended validation plan for an opportunity."""
    # Get opportunity
    query = select(Opportunity).where(Opportunity.id == opportunity_id)
    result = await session.execute(query)
    opportunity = result.scalar_one_or_none()

    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    # Get recommendation
    recommender = ValidationRecommender()
    plan = recommender.recommend(
        budget=request.budget,
        time_available=request.time_available,
        risk_tolerance=request.risk_tolerance,
        payment_intent=opportunity.payment_signal_strength,
        success_prediction=opportunity.success_prediction,
        product_type=opportunity.product_type,
    )

    return {
        "opportunity_id": opportunity_id,
        "plan": {
            "steps": [
                {
                    "priority": step.priority,
                    "tool": {
                        "tool_type": step.tool.tool_type.value,
                        "name": step.tool.name,
                        "description": step.tool.description,
                        "cost_estimate_min": step.tool.cost_estimate_min,
                        "cost_estimate_max": step.tool.cost_estimate_max,
                        "time_estimate_days": step.tool.time_estimate_days,
                        "difficulty": step.tool.difficulty,
                    },
                    "reasoning": step.reasoning,
                    "expected_outcome": step.expected_outcome,
                    "risk_mitigation": step.risk_mitigation,
                }
                for step in plan.steps
            ],
            "total_cost_min": plan.total_cost_min,
            "total_cost_max": plan.total_cost_max,
            "total_time_days": plan.total_time_days,
            "confidence_level": plan.confidence_level,
            "overall_strategy": plan.overall_strategy,
        },
    }


@router.delete("/validation/{tracker_id}")
async def delete_validation_tracker(
    tracker_id: int, session: AsyncSession = Depends(get_session)
):
    """Delete a validation tracker."""
    query = select(ValidationTracker).where(ValidationTracker.id == tracker_id)
    result = await session.execute(query)
    tracker = result.scalar_one_or_none()

    if not tracker:
        raise HTTPException(status_code=404, detail="Validation tracker not found")

    await session.delete(tracker)
    await session.commit()

    return {"message": "Validation tracker deleted", "id": tracker_id}
