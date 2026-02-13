from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, or_

from app.database import get_session, User
from app.api.auth import get_current_user
from app.models.app_store import (
    AppStoreSavedSearch,
    AppStoreApp,
    AppStoreCategory,
    AppScore,
)

router = APIRouter(prefix="/app-store/saved-searches")


class AppStoreSearchCriteria(BaseModel):
    category: Optional[str] = None
    min_score: Optional[float] = Field(None, ge=0, le=100)
    is_rising: Optional[bool] = None
    is_new: Optional[bool] = None
    price_range: Optional[Dict[str, float]] = None
    sort_by: Optional[str] = None
    keywords: Optional[List[str]] = None


class AppStoreSavedSearchCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    criteria: AppStoreSearchCriteria
    notify_on_match: bool = False


class AppStoreSavedSearchUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    criteria: Optional[AppStoreSearchCriteria] = None
    notify_on_match: Optional[bool] = None


class AppStoreSavedSearchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: Optional[str]
    min_score: Optional[float]
    is_rising: Optional[bool]
    is_new: Optional[bool]
    price_range: Optional[Dict[str, float]]
    sort_by: Optional[str]
    keywords: Optional[List[str]]
    notify_on_match: bool
    total_matches: int
    new_matches_today: int
    last_viewed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


@router.post(
    "", response_model=AppStoreSavedSearchResponse, status_code=status.HTTP_201_CREATED
)
async def create_saved_search(
    search_data: AppStoreSavedSearchCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(AppStoreSavedSearch).where(
        AppStoreSavedSearch.user_id == current_user.id
    )
    result = await session.execute(stmt)
    existing_searches = result.scalars().all()

    max_saved_searches = 5

    if len(existing_searches) >= max_saved_searches:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Maximum saved searches ({max_saved_searches}) reached for your plan",
        )

    if search_data.criteria.category:
        cat_stmt = select(AppStoreCategory).where(
            AppStoreCategory.name == search_data.criteria.category
        )
        cat_result = await session.execute(cat_stmt)
        if not cat_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category '{search_data.criteria.category}' not found",
            )

    saved_search = AppStoreSavedSearch(
        user_id=current_user.id,
        name=search_data.name,
        category=search_data.criteria.category,
        min_score=search_data.criteria.min_score,
        is_rising=search_data.criteria.is_rising,
        is_new=search_data.criteria.is_new,
        price_range=search_data.criteria.price_range,
        sort_by=search_data.criteria.sort_by,
        keywords=search_data.criteria.keywords,
        notify_on_match=search_data.notify_on_match,
    )

    session.add(saved_search)
    await session.commit()
    await session.refresh(saved_search)

    return AppStoreSavedSearchResponse.model_validate(saved_search)


@router.get("", response_model=List[AppStoreSavedSearchResponse])
async def list_saved_searches(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(AppStoreSavedSearch).where(
        AppStoreSavedSearch.user_id == current_user.id
    )
    result = await session.execute(stmt)
    searches = result.scalars().all()
    return [AppStoreSavedSearchResponse.model_validate(search) for search in searches]


@router.get("/{search_id}", response_model=AppStoreSavedSearchResponse)
async def get_saved_search(
    search_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(AppStoreSavedSearch).where(
        and_(
            AppStoreSavedSearch.id == search_id,
            AppStoreSavedSearch.user_id == current_user.id,
        )
    )
    result = await session.execute(stmt)
    saved_search = result.scalar_one_or_none()

    if not saved_search:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Saved search not found"
        )

    setattr(saved_search, "last_viewed_at", datetime.now(timezone.utc))
    await session.commit()

    return AppStoreSavedSearchResponse.model_validate(saved_search)


@router.post("/{search_id}/matches")
async def get_saved_search_matches(
    search_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    search_stmt = select(AppStoreSavedSearch).where(
        and_(
            AppStoreSavedSearch.id == search_id,
            AppStoreSavedSearch.user_id == current_user.id,
        )
    )
    search_result = await session.execute(search_stmt)
    saved_search = search_result.scalar_one_or_none()

    if not saved_search:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Saved search not found"
        )

    base_query = select(AppStoreApp).join(AppScore, AppStoreApp.id == AppScore.app_id)

    conditions = []

    if getattr(saved_search, "category", None):
        cat_stmt = select(AppStoreCategory.id).where(
            AppStoreCategory.name == getattr(saved_search, "category")
        )
        cat_result = await session.execute(cat_stmt)
        cat_ids = [row[0] for row in cat_result.fetchall()]
        if cat_ids:
            conditions.append(AppStoreApp.category_id.in_(cat_ids))

    if getattr(saved_search, "min_score", None) is not None:
        conditions.append(
            AppScore.total_opportunity_score >= getattr(saved_search, "min_score")
        )

    if getattr(saved_search, "is_rising", None):
        conditions.append(AppStoreApp.is_rising == True)

    if getattr(saved_search, "is_new", None):
        conditions.append(AppStoreApp.is_new_release == True)

    price_range = getattr(saved_search, "price_range", None)
    if price_range:
        if price_range.get("min") is not None:
            conditions.append(AppStoreApp.price >= price_range["min"])
        if price_range.get("max") is not None:
            conditions.append(AppStoreApp.price <= price_range["max"])

    keywords = getattr(saved_search, "keywords", None)
    if keywords:
        keyword_conditions = []
        for keyword in keywords:
            keyword_conditions.append(AppStoreApp.name.ilike(f"%{keyword}%"))
            keyword_conditions.append(AppStoreApp.description.ilike(f"%{keyword}%"))
            keyword_conditions.append(AppStoreApp.developer.ilike(f"%{keyword}%"))
        if keyword_conditions:
            conditions.append(or_(*keyword_conditions))

    if conditions:
        for condition in conditions:
            base_query = base_query.where(condition)

    count_query = select(func.count()).select_from(base_query.subquery())
    count_result = await session.execute(count_query)
    total_count = count_result.scalar() or 0

    sort_column = getattr(saved_search, "sort_by") or "total_score"
    if sort_column == "total_score":
        base_query = base_query.order_by(AppScore.total_opportunity_score.desc())
    elif sort_column == "rating":
        base_query = base_query.order_by(AppStoreApp.rating.desc())
    elif sort_column == "revenue_potential":
        base_query = base_query.order_by(AppScore.revenue_potential_score.desc())
    else:
        base_query = base_query.order_by(AppStoreApp.engagement_score.desc())

    offset = (page - 1) * page_size
    base_query = base_query.offset(offset).limit(page_size)

    result = await session.execute(base_query)
    apps = result.scalars().all()

    setattr(saved_search, "total_matches", total_count)
    await session.commit()

    items = []
    for app in apps:
        items.append(
            {
                "id": app.id,
                "name": app.name,
                "developer": app.developer,
                "icon_url": app.icon_url,
                "price": app.price,
                "rating": app.rating,
                "is_rising": app.is_rising,
                "is_new_release": app.is_new_release,
                "app_store_url": app.app_store_url,
            }
        )

    return {
        "items": items,
        "total": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": (total_count + page_size - 1) // page_size,
    }


@router.patch("/{search_id}", response_model=AppStoreSavedSearchResponse)
async def update_saved_search(
    search_id: int,
    search_data: AppStoreSavedSearchUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(AppStoreSavedSearch).where(
        and_(
            AppStoreSavedSearch.id == search_id,
            AppStoreSavedSearch.user_id == current_user.id,
        )
    )
    result = await session.execute(stmt)
    saved_search = result.scalar_one_or_none()

    if not saved_search:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Saved search not found"
        )

    if search_data.name is not None:
        setattr(saved_search, "name", search_data.name)
    if search_data.notify_on_match is not None:
        setattr(saved_search, "notify_on_match", search_data.notify_on_match)

    if search_data.criteria is not None:
        if search_data.criteria.category is not None:
            if search_data.criteria.category:
                cat_stmt = select(AppStoreCategory).where(
                    AppStoreCategory.name == search_data.criteria.category
                )
                cat_result = await session.execute(cat_stmt)
                if not cat_result.scalar_one_or_none():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Category '{search_data.criteria.category}' not found",
                    )
            setattr(saved_search, "category", search_data.criteria.category)

        if search_data.criteria.min_score is not None:
            setattr(saved_search, "min_score", search_data.criteria.min_score)
        if search_data.criteria.is_rising is not None:
            setattr(saved_search, "is_rising", search_data.criteria.is_rising)
        if search_data.criteria.is_new is not None:
            setattr(saved_search, "is_new", search_data.criteria.is_new)
        if search_data.criteria.price_range is not None:
            setattr(saved_search, "price_range", search_data.criteria.price_range)
        if search_data.criteria.sort_by is not None:
            setattr(saved_search, "sort_by", search_data.criteria.sort_by)
        if search_data.criteria.keywords is not None:
            setattr(saved_search, "keywords", search_data.criteria.keywords)

    await session.commit()
    await session.refresh(saved_search)

    return AppStoreSavedSearchResponse.model_validate(saved_search)


@router.delete("/{search_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_saved_search(
    search_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(AppStoreSavedSearch).where(
        and_(
            AppStoreSavedSearch.id == search_id,
            AppStoreSavedSearch.user_id == current_user.id,
        )
    )
    result = await session.execute(stmt)
    saved_search = result.scalar_one_or_none()

    if not saved_search:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Saved search not found"
        )

    await session.delete(saved_search)
    await session.commit()

    return None
