"""Export API endpoints."""

import csv
import io
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import Opportunity, get_session
from app.middleware.rate_limit import limiter

router = APIRouter()


@router.get("/csv")
@limiter.limit("10/minute")
async def export_csv(
    request: Request,
    status: str | None = Query(None),
    min_score: float | None = Query(None, ge=0, le=10),
    session: AsyncSession = Depends(get_session),
):
    """Export opportunities to CSV."""
    query = select(Opportunity).options(selectinload(Opportunity.raw_post))

    if status:
        query = query.where(Opportunity.status == status)
    if min_score is not None:
        query = query.where(Opportunity.total_score >= min_score)

    query = query.order_by(Opportunity.total_score.desc().nullslast())

    result = await session.execute(query)
    opportunities = result.scalars().all()

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(
        [
            "ID",
            "Title",
            "Summary",
            "Product Type",
            "Sector",
            "Business Model",
            "Demand Score",
            "Market Score",
            "Feasibility Score",
            "Revenue Score",
            "Total Score",
            "Confidence",
            "Status",
            "Source",
            "Source URL",
            "Created At",
        ]
    )

    # Data
    for opp in opportunities:
        writer.writerow(
            [
                opp.id,
                opp.title,
                opp.summary,
                opp.product_type,
                opp.sector,
                opp.business_model,
                opp.demand_score,
                opp.market_score,
                opp.feasibility_score,
                opp.revenue_score,
                opp.total_score,
                opp.confidence,
                opp.status,
                opp.raw_post.source if opp.raw_post else None,
                opp.raw_post.url if opp.raw_post else None,
                opp.created_at.isoformat() if opp.created_at else None,
            ]
        )

    output.seek(0)
    filename = (
        f"opportunities_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
    )

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/json")
@limiter.limit("10/minute")
async def export_json(
    request: Request,
    status: str | None = Query(None),
    min_score: float | None = Query(None, ge=0, le=10),
    session: AsyncSession = Depends(get_session),
):
    """Export opportunities to JSON."""
    query = select(Opportunity).options(selectinload(Opportunity.raw_post))

    if status:
        query = query.where(Opportunity.status == status)
    if min_score is not None:
        query = query.where(Opportunity.total_score >= min_score)

    query = query.order_by(Opportunity.total_score.desc().nullslast())

    result = await session.execute(query)
    opportunities = result.scalars().all()

    data = []
    for opp in opportunities:
        data.append(
            {
                "id": opp.id,
                "title": opp.title,
                "summary": opp.summary,
                "product_type": opp.product_type,
                "sector": opp.sector,
                "business_model": opp.business_model,
                "scores": {
                    "demand": opp.demand_score,
                    "market": opp.market_score,
                    "feasibility": opp.feasibility_score,
                    "revenue": opp.revenue_score,
                    "total": opp.total_score,
                    "confidence": opp.confidence,
                },
                "competitors": opp.competitors,
                "suggested_features": opp.suggested_features,
                "go_to_market": opp.go_to_market,
                "status": opp.status,
                "notes": opp.notes,
                "source": {
                    "name": opp.raw_post.source if opp.raw_post else None,
                    "url": opp.raw_post.url if opp.raw_post else None,
                    "content": opp.raw_post.content if opp.raw_post else None,
                },
                "created_at": opp.created_at.isoformat() if opp.created_at else None,
            }
        )

    output = json.dumps(data, indent=2)
    filename = (
        f"opportunities_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    )

    return StreamingResponse(
        iter([output]),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
