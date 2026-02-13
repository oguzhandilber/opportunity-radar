"""App Store API endpoints."""

import math
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_session
from app.middleware.auth import verify_api_key
from app.models.app_store import AppStoreApp, AppStoreCategory, AppScore

router = APIRouter(prefix="/app-store", tags=["App Store"])


@router.get("/categories")
async def get_categories(
    session: AsyncSession = Depends(get_session),
) -> List[Dict[str, Any]]:
    """Get all App Store categories."""
    query = select(AppStoreCategory)
    result = await session.execute(query)
    categories = result.scalars().all()

    return [
        {
            "id": cat.id,
            "name": cat.name,
            "apple_id": cat.apple_id,
            "app_count": cat.app_count,
            "average_rating": cat.average_rating,
            "revenue_benchmark": cat.revenue_benchmark,
            "complexity_multiplier": cat.complexity_multiplier,
        }
        for cat in categories
    ]


@router.get("/apps")
async def get_apps(
    category: Optional[str] = Query(None, description="Filter by category name"),
    min_score: Optional[float] = Query(
        None, ge=0, le=100, description="Minimum total opportunity score"
    ),
    is_rising: Optional[bool] = Query(None, description="Only rising apps"),
    is_new: Optional[bool] = Query(None, description="Only newly released apps"),
    min_rating: Optional[float] = Query(None, ge=0, le=5, description="Minimum rating"),
    max_rating: Optional[float] = Query(None, ge=0, le=5, description="Maximum rating"),
    free_only: Optional[bool] = Query(None, description="Only free apps"),
    paid_only: Optional[bool] = Query(None, description="Only paid apps"),
    sort_by: Optional[str] = Query(
        "total_score",
        description="Sort field: total_score, rating, rising_score, revenue_potential",
    ),
    sort_order: Optional[str] = Query("desc", description="Sort order: asc, desc"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    session: AsyncSession = Depends(get_session),
) -> Dict[str, Any]:
    """Get filtered and paginated list of App Store apps."""

    # Build base query
    base_query = select(AppStoreApp).options(selectinload(AppStoreApp.category))

    # Apply filters
    conditions = []

    if category:
        cat_query = select(AppStoreCategory.id).where(AppStoreCategory.name == category)
        cat_result = await session.execute(cat_query)
        cat_ids = [row[0] for row in cat_result.fetchall()]
        if cat_ids:
            conditions.append(AppStoreApp.category_id.in_(cat_ids))

    if is_rising:
        conditions.append(AppStoreApp.is_rising == True)

    if is_new:
        conditions.append(AppStoreApp.is_new_release == True)

    if min_rating is not None:
        conditions.append(AppStoreApp.rating >= min_rating)

    if max_rating is not None:
        conditions.append(AppStoreApp.rating <= max_rating)

    if free_only:
        conditions.append(AppStoreApp.price == 0)

    if paid_only:
        conditions.append(AppStoreApp.price > 0)

    # Apply conditions
    if conditions:
        for condition in conditions:
            base_query = base_query.where(condition)

    # Get total count
    count_query = select(func.count()).select_from(base_query.subquery())
    count_result = await session.execute(count_query)
    total_count = count_result.scalar() or 0

    # Apply sorting
    if sort_by == "total_score":
        # Join with scores for total_score sorting
        base_query = base_query.join(AppScore, AppStoreApp.id == AppScore.app_id)
        sort_column = AppScore.total_opportunity_score
    elif sort_by == "rating":
        sort_column = AppStoreApp.rating
    elif sort_by == "rising_score":
        base_query = base_query.join(AppScore, AppStoreApp.id == AppScore.app_id)
        sort_column = AppScore.rising_score
    elif sort_by == "revenue_potential":
        base_query = base_query.join(AppScore, AppStoreApp.id == AppScore.app_id)
        sort_column = AppScore.revenue_potential_score
    else:
        # Default to engagement_score
        sort_column = AppStoreApp.engagement_score

    if sort_order == "desc":
        base_query = base_query.order_by(sort_column.desc())
    else:
        base_query = base_query.order_by(sort_column.asc())

    # Apply pagination
    offset = (page - 1) * page_size
    base_query = base_query.offset(offset).limit(page_size)

    # Execute query
    result = await session.execute(base_query)
    apps = result.scalars().unique().all()

    # Get scores for apps
    app_ids = [app.id for app in apps]
    scores_map = {}
    if app_ids:
        scores_query = select(AppScore).where(AppScore.app_id.in_(app_ids))
        scores_result = await session.execute(scores_query)
        for score in scores_result.scalars().all():
            scores_map[score.app_id] = score

    # Build response
    items = []
    for app in apps:
        score = scores_map.get(app.id)

        item = {
            "id": app.id,
            "apple_app_id": app.apple_app_id,
            "name": app.name,
            "developer": app.developer,
            "description": app.description,
            "icon_url": app.icon_url,
            "app_store_url": app.app_store_url,
            "price": app.price,
            "rating": app.rating,
            "rating_count": app.rating_count,
            "category": app.category.name if app.category else None,
            "is_rising": app.is_rising,
            "is_new_release": app.is_new_release,
            "trend_direction": app.trend_direction,
            "engagement_score": app.engagement_score,
            "created_at": app.created_at.isoformat()
            if app.created_at is not None
            else None,
            "scraped_at": app.scraped_at.isoformat()
            if app.scraped_at is not None
            else None,
        }

        if score:
            item["scores"] = {
                "build_ease_score": score.build_ease_score,
                "revenue_potential_score": score.revenue_potential_score,
                "market_opportunity_score": score.market_opportunity_score,
                "rising_score": score.rising_score,
                "total_opportunity_score": score.total_opportunity_score,
                "confidence_score": score.confidence_score,
                "opportunity_summary": score.opportunity_summary,
            }
        else:
            item["scores"] = None

        items.append(item)

    return {
        "items": items,
        "total": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": math.ceil(total_count / page_size) if total_count > 0 else 0,
    }


@router.get("/apps/{app_id}")
async def get_app_details(
    app_id: int,
    session: AsyncSession = Depends(get_session),
) -> Dict[str, Any]:
    """Get detailed information for a specific app."""
    query = (
        select(AppStoreApp)
        .options(
            selectinload(AppStoreApp.category),
            selectinload(AppStoreApp.scores),
            selectinload(AppStoreApp.trend_history),
        )
        .where(AppStoreApp.id == app_id)
    )

    result = await session.execute(query)
    app = result.scalar_one_or_none()

    if not app:
        raise HTTPException(status_code=404, detail="App not found")

    response = {
        "id": app.id,
        "apple_app_id": app.apple_app_id,
        "name": app.name,
        "developer": app.developer,
        "description": app.description,
        "icon_url": app.icon_url,
        "screenshot_urls": app.screenshot_urls,
        "app_store_url": app.app_store_url,
        "price": app.price,
        "currency": app.currency,
        "rating": app.rating,
        "rating_count": app.rating_count,
        "current_rating_count": app.current_rating_count,
        "category": {
            "id": app.category.id,
            "name": app.category.name,
            "revenue_benchmark": app.category.revenue_benchmark,
            "complexity_multiplier": app.category.complexity_multiplier,
        }
        if app.category
        else None,
        "content_rating": app.content_rating,
        "languages": app.languages,
        "release_date": app.release_date.isoformat()
        if app.release_date is not None
        else None,
        "last_updated": app.last_updated.isoformat()
        if app.last_updated is not None
        else None,
        "age_in_days": app.age_in_days,
        "is_rising": app.is_rising,
        "is_new_release": app.is_new_release,
        "trend_direction": app.trend_direction,
        "download_estimate": app.download_estimate,
        "active_user_estimate": app.active_user_estimate,
        "engagement_score": app.engagement_score,
        "created_at": app.created_at.isoformat() if app.created_at else None,
        "scraped_at": app.scraped_at.isoformat() if app.scraped_at else None,
    }

    if app.scores:
        response["scores"] = {
            "build_ease_score": app.scores.build_ease_score,
            "build_ease_factors": app.scores.build_ease_factors,
            "revenue_potential_score": app.scores.revenue_potential_score,
            "revenue_factors": app.scores.revenue_factors,
            "market_opportunity_score": app.scores.market_opportunity_score,
            "market_factors": app.scores.market_factors,
            "rising_score": app.scores.rising_score,
            "rising_factors": app.scores.rising_factors,
            "total_opportunity_score": app.scores.total_opportunity_score,
            "confidence_score": app.scores.confidence_score,
            "analysis_text": app.scores.analysis_text,
            "opportunity_summary": app.scores.opportunity_summary,
            "scored_at": app.scores.scored_at.isoformat()
            if app.scores.scored_at
            else None,
        }
    else:
        response["scores"] = None

    # Add trend history
    if app.trend_history:
        response["trend_history"] = [
            {
                "date": th.recorded_at.isoformat() if th.recorded_at else None,
                "ranking": th.ranking,
                "rating": th.rating,
                "rating_velocity": th.rating_velocity,
                "ranking_change": th.ranking_change,
            }
            for th in sorted(
                app.trend_history,
                key=lambda x: x.recorded_at or datetime.min,
                reverse=True,
            )[:30]
        ]
    else:
        response["trend_history"] = []

    return response


@router.get("/trending")
async def get_trending_apps(
    timeframe: Optional[str] = Query("7d", description="Timeframe: 24h, 7d, 30d"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(20, ge=1, le=100, description="Number of apps to return"),
    session: AsyncSession = Depends(get_session),
) -> List[Dict[str, Any]]:
    """Get trending/rising apps."""

    base_query = (
        select(AppStoreApp)
        .options(selectinload(AppStoreApp.category), selectinload(AppStoreApp.scores))
        .where(AppStoreApp.is_rising == True)
    )

    # Filter by category if provided
    if category:
        cat_query = select(AppStoreCategory.id).where(AppStoreCategory.name == category)
        cat_result = await session.execute(cat_query)
        cat_ids = [row[0] for row in cat_result.fetchall()]
        if cat_ids:
            base_query = base_query.where(AppStoreApp.category_id.in_(cat_ids))

    # Order by rising score
    base_query = base_query.order_by(AppStoreApp.engagement_score.desc()).limit(limit)

    result = await session.execute(base_query)
    apps = result.scalars().unique().all()

    return [
        {
            "id": app.id,
            "name": app.name,
            "developer": app.developer,
            "icon_url": app.icon_url,
            "rating": app.rating,
            "category": app.category.name if app.category else None,
            "engagement_score": app.engagement_score,
            "trend_direction": app.trend_direction,
            "total_opportunity_score": app.scores.total_opportunity_score
            if app.scores
            else None,
            "rising_score": app.scores.rising_score if app.scores else None,
        }
        for app in apps
    ]


@router.get("/opportunities")
async def get_opportunities(
    min_score: float = Query(
        60.0, ge=0, le=100, description="Minimum total opportunity score"
    ),
    focus_area: Optional[str] = Query(
        None, description="Focus area: revenue, market, rising, easy_build"
    ),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(50, ge=1, le=100, description="Number of apps to return"),
    session: AsyncSession = Depends(get_session),
) -> List[Dict[str, Any]]:
    """Get high-opportunity apps based on scores."""

    base_query = (
        select(AppStoreApp)
        .options(selectinload(AppStoreApp.category), selectinload(AppStoreApp.scores))
        .join(AppScore, AppStoreApp.id == AppScore.app_id)
        .where(AppScore.total_opportunity_score >= min_score)
    )

    # Filter by category
    if category:
        cat_query = select(AppStoreCategory.id).where(AppStoreCategory.name == category)
        cat_result = await session.execute(cat_query)
        cat_ids = [row[0] for row in cat_result.fetchall()]
        if cat_ids:
            base_query = base_query.where(AppStoreApp.category_id.in_(cat_ids))

    # Sort by focus area
    if focus_area == "revenue":
        base_query = base_query.order_by(AppScore.revenue_potential_score.desc())
    elif focus_area == "market":
        base_query = base_query.order_by(AppScore.market_opportunity_score.desc())
    elif focus_area == "rising":
        base_query = base_query.order_by(AppScore.rising_score.desc())
    elif focus_area == "easy_build":
        base_query = base_query.order_by(AppScore.build_ease_score.desc())
    else:
        base_query = base_query.order_by(AppScore.total_opportunity_score.desc())

    base_query = base_query.limit(limit)

    result = await session.execute(base_query)
    apps = result.scalars().unique().all()

    return [
        {
            "id": app.id,
            "name": app.name,
            "developer": app.developer,
            "icon_url": app.icon_url,
            "category": app.category.name if app.category else None,
            "price": app.price,
            "rating": app.rating,
            "total_opportunity_score": app.scores.total_opportunity_score
            if app.scores
            else None,
            "revenue_potential_score": app.scores.revenue_potential_score
            if app.scores
            else None,
            "market_opportunity_score": app.scores.market_opportunity_score
            if app.scores
            else None,
            "rising_score": app.scores.rising_score if app.scores else None,
            "build_ease_score": app.scores.build_ease_score if app.scores else None,
            "opportunity_summary": app.scores.opportunity_summary
            if app.scores
            else None,
            "app_store_url": app.app_store_url,
        }
        for app in apps
    ]


@router.get("/stats")
async def get_stats(
    session: AsyncSession = Depends(get_session),
) -> Dict[str, Any]:
    """Get overall App Store stats."""

    # Total apps
    total_query = select(func.count()).select_from(AppStoreApp)
    total_result = await session.execute(total_query)
    total_apps = total_result.scalar() or 0

    # Apps with scores
    scored_query = select(func.count()).select_from(AppScore)
    scored_result = await session.execute(scored_query)
    scored_apps = scored_result.scalar() or 0

    # Rising apps
    rising_query = select(func.count()).where(AppStoreApp.is_rising == True)
    rising_result = await session.execute(rising_query)
    rising_apps = rising_result.scalar() or 0

    # New releases
    new_query = select(func.count()).where(AppStoreApp.is_new_release == True)
    new_result = await session.execute(new_query)
    new_releases = new_result.scalar() or 0

    # Average scores
    avg_query = select(
        func.avg(AppScore.total_opportunity_score),
        func.avg(AppScore.revenue_potential_score),
        func.avg(AppScore.market_opportunity_score),
        func.avg(AppScore.rising_score),
        func.avg(AppScore.build_ease_score),
    )
    avg_result = await session.execute(avg_query)
    avg_scores = avg_result.fetchone()

    # Category breakdown
    cat_query = (
        select(AppStoreCategory.name, func.count())
        .join(AppStoreApp, AppStoreApp.category_id == AppStoreCategory.id)
        .group_by(AppStoreCategory.name)
        .order_by(func.count().desc())
    )
    cat_result = await session.execute(cat_query)
    category_breakdown = [
        {"name": row[0], "count": row[1]} for row in cat_result.fetchall()
    ]

    return {
        "total_apps": total_apps,
        "scored_apps": scored_apps,
        "rising_apps": rising_apps,
        "new_releases": new_releases,
        "scoring_coverage": round(scored_apps / total_apps * 100, 1)
        if total_apps > 0
        else 0,
        "average_scores": {
            "total_opportunity": round(avg_scores[0], 1)
            if avg_scores and avg_scores[0]
            else None,
            "revenue_potential": round(avg_scores[1], 1)
            if avg_scores and avg_scores[1]
            else None,
            "market_opportunity": round(avg_scores[2], 1)
            if avg_scores and avg_scores[2]
            else None,
            "rising": round(avg_scores[3], 1) if avg_scores and avg_scores[3] else None,
            "build_ease": round(avg_scores[4], 1)
            if avg_scores and avg_scores[4]
            else None,
        },
        "categories": category_breakdown,
    }


@router.post("/scrape")
async def trigger_scrape():
    """Trigger App Store scraping job."""
    from app.scrapers.app_store import run_app_store_scraper

    # Start scraping in background
    import asyncio

    asyncio.create_task(run_app_store_scraper())

    return {
        "status": "started",
        "message": "Scraping job started. This will take several minutes.",
    }


@router.post("/score")
async def trigger_scoring():
    """Trigger scoring for unscored apps."""
    from app.services.app_scoring import AppScoringService

    async def run_scoring():
        service = AppScoringService()
        return await service.score_all_apps()

    import asyncio

    task = asyncio.create_task(run_scoring())

    return {
        "status": "started",
        "message": "Scoring job started. This may take several minutes.",
    }


@router.get("/apps/{app_id}/revenue")
async def get_app_revenue(
    app_id: int,
    session: AsyncSession = Depends(get_session),
) -> Dict[str, Any]:
    """Get revenue estimate for a specific app."""
    # Get app with category
    query = (
        select(AppStoreApp)
        .options(selectinload(AppStoreApp.category))
        .where(AppStoreApp.id == app_id)
    )

    result = await session.execute(query)
    app = result.scalar_one_or_none()

    if not app:
        raise HTTPException(status_code=404, detail="App not found")

    # Use RevenueEstimationService to calculate estimate
    from app.services.revenue_estimation import RevenueEstimationService

    service = RevenueEstimationService()
    estimate = await service.estimate_revenue(app)

    return {
        "app_id": app.id,
        "app_name": app.name,
        "category": app.category.name if app.category else None,
        "revenue_estimate": estimate,
    }


@router.get("/revenue/leaderboard")
async def get_revenue_leaderboard(
    limit: int = Query(50, ge=1, le=100),
    category: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
) -> List[Dict[str, Any]]:
    """Get top apps by revenue estimate."""

    # Build base query
    base_query = select(AppStoreApp).options(selectinload(AppStoreApp.category))

    # Filter by category if provided
    if category:
        cat_query = select(AppStoreCategory.id).where(AppStoreCategory.name == category)
        cat_result = await session.execute(cat_query)
        cat_ids = [row[0] for row in cat_result.fetchall()]
        if cat_ids:
            base_query = base_query.where(AppStoreApp.category_id.in_(cat_ids))
        else:
            # Category not found, return empty list
            return []

    # Filter to apps with revenue estimates
    base_query = base_query.where(AppStoreApp.monthly_revenue_estimate.isnot(None))

    # Order by monthly revenue estimate (descending)
    base_query = base_query.order_by(AppStoreApp.monthly_revenue_estimate.desc()).limit(
        limit
    )

    result = await session.execute(base_query)
    apps = result.scalars().all()

    return [
        {
            "id": app.id,
            "name": app.name,
            "developer": app.developer,
            "category": app.category.name if app.category else None,
            "monthly_revenue_estimate": app.monthly_revenue_estimate,
            "yearly_revenue_estimate": app.yearly_revenue_estimate,
            "revenue_confidence": app.revenue_confidence,
            "download_estimate": app.download_estimate,
            "rating": app.rating,
            "rating_count": app.rating_count,
            "price": app.price,
        }
        for app in apps
    ]


@router.get("/revenue/stats")
async def get_revenue_stats(
    category: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
) -> Dict[str, Any]:
    """Get revenue statistics across apps."""

    # Base query for apps with revenue estimates
    base_query = select(AppStoreApp).options(selectinload(AppStoreApp.category))

    # Filter by category if provided
    if category:
        cat_query = select(AppStoreCategory.id).where(AppStoreCategory.name == category)
        cat_result = await session.execute(cat_query)
        cat_ids = [row[0] for row in cat_result.fetchall()]
        if cat_ids:
            base_query = base_query.where(AppStoreApp.category_id.in_(cat_ids))
        else:
            # Category not found, return empty stats
            return {
                "total_apps": 0,
                "apps_with_estimates": 0,
                "total_monthly_revenue": 0,
                "total_yearly_revenue": 0,
                "average_monthly_revenue": 0,
                "average_yearly_revenue": 0,
                "median_monthly_revenue": 0,
                "top_monthly_revenue": 0,
                "revenue_distribution": {},
            }

    # Filter to apps with revenue estimates
    base_query = base_query.where(AppStoreApp.monthly_revenue_estimate.isnot(None))

    result = await session.execute(base_query)
    apps = result.scalars().all()

    if not apps:
        return {
            "total_apps": 0,
            "apps_with_estimates": 0,
            "total_monthly_revenue": 0,
            "total_yearly_revenue": 0,
            "average_monthly_revenue": 0,
            "average_yearly_revenue": 0,
            "median_monthly_revenue": 0,
            "top_monthly_revenue": 0,
            "revenue_distribution": {},
        }

    # Calculate statistics
    monthly_revenues = [app.monthly_revenue_estimate or 0 for app in apps]
    yearly_revenues = [app.yearly_revenue_estimate or 0 for app in apps]

    total_monthly = sum(monthly_revenues)
    total_yearly = sum(yearly_revenues)
    avg_monthly = total_monthly / len(apps)
    avg_yearly = total_yearly / len(apps)

    # Calculate median
    sorted_monthly = sorted(monthly_revenues)
    median_monthly = (
        sorted_monthly[len(sorted_monthly) // 2]
        if len(sorted_monthly) % 2 == 1
        else (
            sorted_monthly[len(sorted_monthly) // 2 - 1]
            + sorted_monthly[len(sorted_monthly) // 2]
        )
        / 2
    )

    top_monthly = max(monthly_revenues)

    # Revenue distribution buckets
    distribution = {
        "under_1k": sum(1 for r in monthly_revenues if r < 1000),
        "1k_to_5k": sum(1 for r in monthly_revenues if 1000 <= r < 5000),
        "5k_to_10k": sum(1 for r in monthly_revenues if 5000 <= r < 10000),
        "10k_to_50k": sum(1 for r in monthly_revenues if 10000 <= r < 50000),
        "50k_to_100k": sum(1 for r in monthly_revenues if 50000 <= r < 100000),
        "over_100k": sum(1 for r in monthly_revenues if r >= 100000),
    }

    return {
        "total_apps": len(apps),
        "apps_with_estimates": len(apps),
        "total_monthly_revenue": round(total_monthly, 2),
        "total_yearly_revenue": round(total_yearly, 2),
        "average_monthly_revenue": round(avg_monthly, 2),
        "average_yearly_revenue": round(avg_yearly, 2),
        "median_monthly_revenue": round(median_monthly, 2),
        "top_monthly_revenue": round(top_monthly, 2),
        "revenue_distribution": distribution,
    }


@router.post("/revenue/estimate-all")
async def estimate_all_revenues():
    """Trigger revenue estimation for all apps."""
    from app.services.revenue_estimation import RevenueEstimationService

    async def run_estimation():
        service = RevenueEstimationService()
        # Run estimation for all apps
        results = await service.estimate_revenue_for_all_apps()
        return results

    import asyncio

    task = asyncio.create_task(run_estimation())

    return {
        "status": "started",
        "message": "Revenue estimation job started. This will take several minutes.",
    }
