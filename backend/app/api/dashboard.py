"""Dashboard API endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Opportunity, RawPost, get_session

router = APIRouter()


@router.get("/stats")
async def get_stats(session: AsyncSession = Depends(get_session)):
    """Get dashboard statistics."""
    # Total opportunities
    total_result = await session.execute(select(func.count(Opportunity.id)))
    total_opportunities = total_result.scalar() or 0

    # New opportunities (status = 'new')
    new_result = await session.execute(
        select(func.count(Opportunity.id)).where(Opportunity.status == "new")
    )
    new_opportunities = new_result.scalar() or 0

    # Saved opportunities
    saved_result = await session.execute(
        select(func.count(Opportunity.id)).where(Opportunity.status == "saved")
    )
    saved_opportunities = saved_result.scalar() or 0

    # Total raw posts
    posts_result = await session.execute(select(func.count(RawPost.id)))
    total_posts = posts_result.scalar() or 0

    # Average scores
    avg_result = await session.execute(
        select(func.avg(Opportunity.total_score)).where(Opportunity.total_score.isnot(None))
    )
    avg_score = avg_result.scalar() or 0

    # Top sectors
    sector_result = await session.execute(
        select(Opportunity.sector, func.count(Opportunity.id).label("count"))
        .where(Opportunity.sector.isnot(None))
        .group_by(Opportunity.sector)
        .order_by(func.count(Opportunity.id).desc())
        .limit(5)
    )
    top_sectors = [{"sector": row[0], "count": row[1]} for row in sector_result.all()]

    # Top product types
    type_result = await session.execute(
        select(Opportunity.product_type, func.count(Opportunity.id).label("count"))
        .where(Opportunity.product_type.isnot(None))
        .group_by(Opportunity.product_type)
        .order_by(func.count(Opportunity.id).desc())
        .limit(5)
    )
    top_product_types = [{"type": row[0], "count": row[1]} for row in type_result.all()]

    return {
        "total_opportunities": total_opportunities,
        "new_opportunities": new_opportunities,
        "saved_opportunities": saved_opportunities,
        "total_posts_scraped": total_posts,
        "average_score": round(avg_score, 2) if avg_score else 0,
        "top_sectors": top_sectors,
        "top_product_types": top_product_types,
    }
