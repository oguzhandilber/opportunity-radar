"""Historical trends API endpoints for opportunity analysis over time."""

from datetime import datetime, timedelta, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload

from app.database import get_session, Opportunity, OpportunityMetricsHistory
from app.api.auth import get_current_user

router = APIRouter()


# Pydantic schemas
class OpportunityMetricsPoint(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    recorded_at: datetime
    total_score: Optional[float]
    demand_score: Optional[float]
    market_score: Optional[float]
    feasibility_score: Optional[float]
    revenue_score: Optional[float]
    mention_count: int
    avg_sentiment: Optional[float]
    momentum_score: Optional[float]
    trend_direction: Optional[str]


class OpportunityTrendResponse(BaseModel):
    opportunity_id: int
    opportunity_title: str
    period: str
    data_points: List[OpportunityMetricsPoint]

    # Aggregated insights
    score_change_7d: Optional[float]
    score_change_30d: Optional[float]
    momentum: str  # accelerating, stable, decelerating
    trend: str  # up, down, stable


class TrendingOpportunitiesResponse(BaseModel):
    rising: List[dict]  # Opportunities with increasing scores
    falling: List[dict]  # Opportunities with decreasing scores
    stable: List[dict]  # Opportunities with stable scores


@router.get(
    "/opportunities/{opportunity_id}/trends", response_model=OpportunityTrendResponse
)
async def get_opportunity_trends(
    opportunity_id: int,
    days: int = Query(30, ge=7, le=365),
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get historical trend data for a specific opportunity."""

    # Check if opportunity exists
    stmt = select(Opportunity).where(Opportunity.id == opportunity_id)
    result = await session.execute(stmt)
    opportunity = result.scalar_one_or_none()

    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found"
        )

    # Get historical metrics
    start_date = datetime.now(timezone.utc) - timedelta(days=days)

    stmt = (
        select(OpportunityMetricsHistory)
        .where(
            and_(
                OpportunityMetricsHistory.opportunity_id == opportunity_id,
                OpportunityMetricsHistory.recorded_at >= start_date,
            )
        )
        .order_by(OpportunityMetricsHistory.recorded_at)
    )

    result = await session.execute(stmt)
    metrics = result.scalars().all()

    if not metrics:
        # Return current opportunity data as single point
        current_point = OpportunityMetricsPoint(
            recorded_at=opportunity.created_at or datetime.now(timezone.utc),
            total_score=opportunity.total_score,
            demand_score=opportunity.demand_score,
            market_score=opportunity.market_score,
            feasibility_score=opportunity.feasibility_score,
            revenue_score=opportunity.revenue_score,
            mention_count=0,
            avg_sentiment=None,
            momentum_score=None,
            trend_direction="stable",
        )

        return OpportunityTrendResponse(
            opportunity_id=opportunity_id,
            opportunity_title=opportunity.title,
            period=f"{days}d",
            data_points=[current_point],
            score_change_7d=None,
            score_change_30d=None,
            momentum="stable",
            trend="stable",
        )

    # Convert to response model
    data_points = [OpportunityMetricsPoint.model_validate(m) for m in metrics]

    # Calculate trends
    score_change_7d = None
    score_change_30d = None

    if len(metrics) >= 2:
        # 7-day change
        recent = metrics[-1]
        week_ago = next(
            (
                m
                for m in reversed(metrics)
                if m.recorded_at <= recent.recorded_at - timedelta(days=7)
            ),
            None,
        )
        if week_ago and week_ago.total_score and recent.total_score:
            score_change_7d = recent.total_score - week_ago.total_score

        # 30-day change
        month_ago = next(
            (
                m
                for m in reversed(metrics)
                if m.recorded_at <= recent.recorded_at - timedelta(days=30)
            ),
            None,
        )
        if month_ago and month_ago.total_score and recent.total_score:
            score_change_30d = recent.total_score - month_ago.total_score

    # Determine momentum and trend
    momentum = "stable"
    trend = "stable"

    if score_change_7d is not None:
        if score_change_7d > 0.5:
            trend = "up"
            momentum = (
                "accelerating"
                if score_change_30d and score_change_30d > 0
                else "stable"
            )
        elif score_change_7d < -0.5:
            trend = "down"
            momentum = (
                "decelerating"
                if score_change_30d and score_change_30d < 0
                else "stable"
            )

    return OpportunityTrendResponse(
        opportunity_id=opportunity_id,
        opportunity_title=opportunity.title,
        period=f"{days}d",
        data_points=data_points,
        score_change_7d=score_change_7d,
        score_change_30d=score_change_30d,
        momentum=momentum,
        trend=trend,
    )


@router.get("/trends/overview", response_model=TrendingOpportunitiesResponse)
async def get_trending_opportunities(
    min_score: float = Query(6.0, ge=0, le=10),
    days: int = Query(7, ge=1, le=30),
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get overview of trending opportunities (rising, falling, stable)."""

    start_date = datetime.now(timezone.utc) - timedelta(days=days)

    # Get opportunities with their latest metrics
    stmt = (
        select(
            Opportunity,
            OpportunityMetricsHistory.total_score,
            OpportunityMetricsHistory.recorded_at,
            OpportunityMetricsHistory.trend_direction,
        )
        .outerjoin(
            OpportunityMetricsHistory,
            Opportunity.id == OpportunityMetricsHistory.opportunity_id,
        )
        .where(
            and_(
                Opportunity.total_score >= min_score,
                OpportunityMetricsHistory.recorded_at >= start_date,
            )
        )
        .order_by(Opportunity.total_score.desc())
    )

    result = await session.execute(stmt)
    rows = result.all()

    rising = []
    falling = []
    stable = []

    for row in rows[:50]:  # Top 50
        opportunity = row[0]
        trend = row[3] or "stable"

        opp_data = {
            "id": opportunity.id,
            "title": opportunity.title,
            "total_score": opportunity.total_score,
            "sector": opportunity.sector,
            "trend": trend,
        }

        if trend == "up":
            rising.append(opp_data)
        elif trend == "down":
            falling.append(opp_data)
        else:
            stable.append(opp_data)

    return TrendingOpportunitiesResponse(
        rising=rising[:10], falling=falling[:10], stable=stable[:10]
    )


@router.post("/metrics/capture")
async def capture_current_metrics(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Capture current metrics for all opportunities (admin endpoint)."""
    # Get all opportunities
    stmt = select(Opportunity)
    result = await session.execute(stmt)
    opportunities = result.scalars().all()

    captured = 0

    for opportunity in opportunities:
        # Create metrics history entry
        metrics = OpportunityMetricsHistory(
            opportunity_id=opportunity.id,
            total_score=opportunity.total_score,
            demand_score=opportunity.demand_score,
            market_score=opportunity.market_score,
            feasibility_score=opportunity.feasibility_score,
            revenue_score=opportunity.revenue_score,
            mention_count=0,  # Could be derived from source data
            period="daily",
            recorded_at=datetime.now(timezone.utc),
        )

        session.add(metrics)
        captured += 1

    await session.commit()

    return {
        "message": f"Captured metrics for {captured} opportunities",
        "captured_count": captured,
    }
