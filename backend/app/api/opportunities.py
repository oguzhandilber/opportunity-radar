"""Opportunities API endpoints."""

from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import Opportunity, RawPost, get_session
from app.middleware.rate_limit import limiter

router = APIRouter()


class OpportunityResponse(BaseModel):
    """Opportunity response model."""

    id: int
    title: str
    summary: str | None
    product_type: str | None
    sector: str | None
    business_model: str | None
    demand_score: float | None
    market_score: float | None
    feasibility_score: float | None
    revenue_score: float | None
    total_score: float | None
    confidence: float | None
    competitors: list | None
    suggested_features: list | None
    go_to_market: str | None
    # Payment Intent fields (Pivot 3)
    payment_signal_tier: int | None
    payment_signal_strength: float | None
    mentioned_prices: list | None
    monthly_price_estimate: float | None
    competitor_mentions: list | None
    churning_from: list | None
    purchase_journey_stage: str | None
    journey_confidence: float | None
    revenue_potential_score: float | None
    # Historical Success Validation (Pivot 4)
    matched_patterns: list | None
    pattern_match_score: float | None
    success_prediction: float | None
    similar_successes: list | None
    success_factors: dict | None
    prediction_confidence: float | None
    risk_level: str | None
    # Niche Focus (Pivot 2)
    detected_niches: list | None
    primary_niche: str | None
    niche_fit_score: float | None
    niche_scores: dict | None
    # Status and metadata
    status: str
    notes: str | None
    created_at: datetime
    updated_at: datetime
    source: str | None = None
    source_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class OpportunityUpdate(BaseModel):
    """Opportunity update model."""

    status: Literal["new", "saved", "rejected", "in_progress"] | None = None
    notes: str | None = Field(None, max_length=5000)


@router.get("")
async def list_opportunities(
    status: str | None = Query(None, description="Filter by status", max_length=20),
    sector: str | None = Query(None, description="Filter by sector", max_length=100),
    product_type: str | None = Query(
        None, description="Filter by product type", max_length=100
    ),
    niche: str | None = Query(None, description="Filter by niche", max_length=50),
    min_score: float | None = Query(
        None, ge=0, le=10, description="Minimum total score"
    ),
    search: str | None = Query(
        None, description="Search in title and summary", max_length=200
    ),
    source: str | None = Query(
        None, description="Filter by source platform", max_length=50
    ),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    """List opportunities with optional filters."""
    # Build base query for filtering
    base_query = select(Opportunity)

    if status:
        base_query = base_query.where(Opportunity.status == status)
    if sector:
        base_query = base_query.where(Opportunity.sector == sector)
    if product_type:
        base_query = base_query.where(Opportunity.product_type == product_type)
    if niche:
        base_query = base_query.where(Opportunity.primary_niche == niche)
    if min_score is not None:
        base_query = base_query.where(Opportunity.total_score >= min_score)
    if search:
        # Escape special LIKE characters to prevent pattern injection
        sanitized_search = (
            search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        )
        search_pattern = f"%{sanitized_search}%"
        base_query = base_query.where(
            (Opportunity.title.ilike(search_pattern))
            | (Opportunity.summary.ilike(search_pattern))
        )
    if source:
        base_query = base_query.join(Opportunity.raw_post).where(
            Opportunity.raw_post.has(source=source)
        )

    # Get total count
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated data
    data_query = base_query.options(selectinload(Opportunity.raw_post))
    data_query = data_query.order_by(Opportunity.total_score.desc().nullslast())
    data_query = data_query.offset(offset).limit(limit)

    result = await session.execute(data_query)
    opportunities = result.scalars().all()

    items = [
        {
            **OpportunityResponse.model_validate(opp).model_dump(),
            "source": opp.raw_post.source if opp.raw_post else None,
            "source_url": opp.raw_post.url if opp.raw_post else None,
        }
        for opp in opportunities
    ]

    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + len(items) < total,
    }


@router.get("/{opportunity_id}")
async def get_opportunity(
    opportunity_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get a single opportunity by ID."""
    query = (
        select(Opportunity)
        .options(selectinload(Opportunity.raw_post))
        .where(Opportunity.id == opportunity_id)
    )
    result = await session.execute(query)
    opportunity = result.scalar_one_or_none()

    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    response = OpportunityResponse.model_validate(opportunity).model_dump()
    if opportunity.raw_post:
        response["source"] = opportunity.raw_post.source
        response["source_url"] = opportunity.raw_post.url
        response["source_content"] = opportunity.raw_post.content
        response["source_author"] = opportunity.raw_post.author
        response["source_engagement"] = opportunity.raw_post.engagement

    return response


@router.patch("/{opportunity_id}")
async def update_opportunity(
    opportunity_id: int,
    update: OpportunityUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Update an opportunity's status or notes."""
    query = select(Opportunity).where(Opportunity.id == opportunity_id)
    result = await session.execute(query)
    opportunity = result.scalar_one_or_none()

    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    if update.status is not None:
        opportunity.status = update.status
    if update.notes is not None:
        opportunity.notes = update.notes

    opportunity.updated_at = datetime.now(timezone.utc)
    await session.commit()

    return {"message": "Opportunity updated", "id": opportunity_id}


@router.delete("/{opportunity_id}")
async def delete_opportunity(
    opportunity_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Delete an opportunity."""
    query = select(Opportunity).where(Opportunity.id == opportunity_id)
    result = await session.execute(query)
    opportunity = result.scalar_one_or_none()

    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    await session.delete(opportunity)
    await session.commit()

    return {"message": "Opportunity deleted", "id": opportunity_id}


@router.post("/{opportunity_id}/analyze")
@limiter.limit("10/minute")
async def deep_analyze(
    request: Request,
    opportunity_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Run deep AI analysis on an opportunity."""
    from app.analyzers.pipeline import deep_analyze_opportunity

    # First check if opportunity exists
    query = select(Opportunity).where(Opportunity.id == opportunity_id)
    result = await session.execute(query)
    opportunity = result.scalar_one_or_none()

    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    # Run deep analysis
    analysis_result = await deep_analyze_opportunity(opportunity_id)

    if "error" in analysis_result:
        raise HTTPException(status_code=500, detail=analysis_result["error"])

    return {
        "message": "Deep analysis completed",
        "id": opportunity_id,
        "analysis": analysis_result.get("analysis", {}),
    }
