"""Saved searches API endpoints."""

from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.database import get_session, SavedSearch, User
from app.api.auth import get_current_user

router = APIRouter()


# Subscription tier limits
TIER_LIMITS = {
    "free": {"saved_searches": 5, "alerts": 3},
    "pro": {"saved_searches": 20, "alerts": 10},
    "team": {"saved_searches": 100, "alerts": 50},
}


def get_user_subscription_tier(user: User) -> str:
    """Get the user's subscription tier from their subscriptions."""
    if not user.subscriptions:
        return "free"

    # Find the active subscription with the highest tier
    tier_priority = {"team": 3, "pro": 2, "free": 1}
    highest_tier = "free"

    for sub in user.subscriptions:
        if sub.status == "active" and sub.plan in tier_priority:
            if tier_priority[sub.plan] > tier_priority.get(highest_tier, 0):
                highest_tier = sub.plan

    return highest_tier


def get_saved_search_limit(user: User) -> int:
    """Get the saved search limit for the user's subscription tier."""
    tier = get_user_subscription_tier(user)
    return TIER_LIMITS.get(tier, TIER_LIMITS["free"])["saved_searches"]


# Pydantic schemas
class SearchCriteria(BaseModel):
    sectors: Optional[List[str]] = None
    product_types: Optional[List[str]] = None
    min_score: Optional[float] = Field(None, ge=0, le=10)
    keywords: Optional[List[str]] = None
    source: Optional[str] = None


class SavedSearchCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    criteria: SearchCriteria


class SavedSearchUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    criteria: Optional[SearchCriteria] = None


class SavedSearchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    sectors: Optional[List[str]]
    product_types: Optional[List[str]]
    min_score: Optional[float]
    keywords: Optional[List[str]]
    source: Optional[str]
    total_matches: int
    new_matches_today: int
    last_viewed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


@router.get("", response_model=List[SavedSearchResponse])
async def list_saved_searches(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List all saved searches for the current user."""
    stmt = select(SavedSearch).where(SavedSearch.user_id == current_user.id)
    result = await session.execute(stmt)
    searches = result.scalars().all()
    return [SavedSearchResponse.model_validate(search) for search in searches]


@router.post(
    "", response_model=SavedSearchResponse, status_code=status.HTTP_201_CREATED
)
async def create_saved_search(
    search_data: SavedSearchCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a new saved search for the current user."""

    # Check subscription limits
    stmt = select(SavedSearch).where(SavedSearch.user_id == current_user.id)
    result = await session.execute(stmt)
    existing_searches = result.scalars().all()

    # Get user's subscription tier limit
    max_saved_searches = get_saved_search_limit(current_user)

    if len(existing_searches) >= max_saved_searches:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You have reached the maximum number of saved searches ({max_saved_searches}) for your plan. Upgrade to create more saved searches.",
        )

    # Create saved search
    saved_search = SavedSearch(
        user_id=current_user.id,
        name=search_data.name,
        sectors=search_data.criteria.sectors,
        product_types=search_data.criteria.product_types,
        min_score=search_data.criteria.min_score,
        keywords=search_data.criteria.keywords,
        source=search_data.criteria.source,
        total_matches=0,
        new_matches_today=0,
    )

    session.add(saved_search)
    await session.commit()
    await session.refresh(saved_search)

    return SavedSearchResponse.model_validate(saved_search)


@router.get("/{search_id}", response_model=SavedSearchResponse)
async def get_saved_search(
    search_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get a specific saved search by ID."""
    stmt = select(SavedSearch).where(
        and_(SavedSearch.id == search_id, SavedSearch.user_id == current_user.id)
    )
    result = await session.execute(stmt)
    saved_search = result.scalar_one_or_none()

    if not saved_search:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Saved search not found"
        )

    # Update last viewed
    saved_search.last_viewed_at = datetime.now(timezone.utc)
    await session.commit()

    return SavedSearchResponse.model_validate(saved_search)


@router.patch("/{search_id}", response_model=SavedSearchResponse)
async def update_saved_search(
    search_id: int,
    search_data: SavedSearchUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Update an existing saved search."""
    stmt = select(SavedSearch).where(
        and_(SavedSearch.id == search_id, SavedSearch.user_id == current_user.id)
    )
    result = await session.execute(stmt)
    saved_search = result.scalar_one_or_none()

    if not saved_search:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Saved search not found"
        )

    # Update fields
    if search_data.name is not None:
        saved_search.name = search_data.name
    if search_data.criteria is not None:
        if search_data.criteria.sectors is not None:
            saved_search.sectors = search_data.criteria.sectors
        if search_data.criteria.product_types is not None:
            saved_search.product_types = search_data.criteria.product_types
        if search_data.criteria.min_score is not None:
            saved_search.min_score = search_data.criteria.min_score
        if search_data.criteria.keywords is not None:
            saved_search.keywords = search_data.criteria.keywords
        if search_data.criteria.source is not None:
            saved_search.source = search_data.criteria.source

    await session.commit()
    await session.refresh(saved_search)

    return SavedSearchResponse.model_validate(saved_search)


@router.delete("/{search_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_saved_search(
    search_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Delete a saved search."""
    stmt = select(SavedSearch).where(
        and_(SavedSearch.id == search_id, SavedSearch.user_id == current_user.id)
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
