"""Alert and notification API endpoints."""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.database import get_session, Alert, User
from app.api.auth import get_current_user

router = APIRouter()


TIER_LIMITS = {
    "free": {"saved_searches": 5, "alerts": 3},
    "pro": {"saved_searches": 20, "alerts": 10},
    "team": {"saved_searches": 100, "alerts": 50},
}


def get_user_subscription_tier(user: User) -> str:
    if not user.subscriptions:
        return "free"
    tier_priority = {"team": 3, "pro": 2, "free": 1}
    highest_tier = "free"
    for sub in user.subscriptions:
        if sub.status == "active" and sub.plan in tier_priority:
            if tier_priority[sub.plan] > tier_priority.get(highest_tier, 0):
                highest_tier = sub.plan
    return highest_tier


def get_alert_limit(user: User) -> int:
    tier = get_user_subscription_tier(user)
    return TIER_LIMITS.get(tier, TIER_LIMITS["free"])["alerts"]


# Pydantic schemas
class AlertCondition(BaseModel):
    min_total_score: Optional[float] = Field(None, ge=0, le=10)
    sectors: Optional[List[str]] = None
    product_types: Optional[List[str]] = None
    keywords: Optional[List[str]] = None


class AlertCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    conditions: AlertCondition
    email_enabled: bool = True
    slack_webhook: Optional[str] = None


class AlertUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    conditions: Optional[AlertCondition] = None
    email_enabled: Optional[bool] = None
    slack_webhook: Optional[str] = None


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    min_total_score: Optional[float]
    sectors: Optional[List[str]]
    product_types: Optional[List[str]]
    keywords: Optional[List[str]]
    email_enabled: bool
    slack_webhook: Optional[str]
    last_alert_at: Optional[datetime]
    created_at: datetime


@router.get("", response_model=List[AlertResponse])
async def list_alerts(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List all alerts for the current user."""
    stmt = select(Alert).where(Alert.user_id == current_user.id)
    result = await session.execute(stmt)
    alerts = result.scalars().all()
    return [AlertResponse.model_validate(alert) for alert in alerts]


@router.post("", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(
    alert_data: AlertCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a new alert for the current user."""

    # Check subscription limits
    stmt = select(Alert).where(Alert.user_id == current_user.id)
    result = await session.execute(stmt)
    existing_alerts = result.scalars().all()

    max_alerts = get_alert_limit(current_user)

    if len(existing_alerts) >= max_alerts:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You have reached the maximum number of alerts ({max_alerts}) for your plan. Upgrade to create more alerts.",
        )

    # Create alert
    alert = Alert(
        user_id=current_user.id,
        name=alert_data.name,
        min_total_score=alert_data.conditions.min_total_score,
        sectors=alert_data.conditions.sectors,
        product_types=alert_data.conditions.product_types,
        keywords=alert_data.conditions.keywords,
        email_enabled=alert_data.email_enabled,
        slack_webhook=alert_data.slack_webhook,
    )

    session.add(alert)
    await session.commit()
    await session.refresh(alert)

    return AlertResponse.model_validate(alert)


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get a specific alert by ID."""
    stmt = select(Alert).where(
        and_(Alert.id == alert_id, Alert.user_id == current_user.id)
    )
    result = await session.execute(stmt)
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found"
        )

    return AlertResponse.model_validate(alert)


@router.patch("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: int,
    alert_data: AlertUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Update an existing alert."""
    stmt = select(Alert).where(
        and_(Alert.id == alert_id, Alert.user_id == current_user.id)
    )
    result = await session.execute(stmt)
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found"
        )

    # Update fields
    if alert_data.name is not None:
        alert.name = alert_data.name
    if alert_data.conditions is not None:
        if alert_data.conditions.min_total_score is not None:
            alert.min_total_score = alert_data.conditions.min_total_score
        if alert_data.conditions.sectors is not None:
            alert.sectors = alert_data.conditions.sectors
        if alert_data.conditions.product_types is not None:
            alert.product_types = alert_data.conditions.product_types
        if alert_data.conditions.keywords is not None:
            alert.keywords = alert_data.conditions.keywords
    if alert_data.email_enabled is not None:
        alert.email_enabled = alert_data.email_enabled
    if alert_data.slack_webhook is not None:
        alert.slack_webhook = alert_data.slack_webhook

    await session.commit()
    await session.refresh(alert)

    return AlertResponse.model_validate(alert)


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Delete an alert."""
    stmt = select(Alert).where(
        and_(Alert.id == alert_id, Alert.user_id == current_user.id)
    )
    result = await session.execute(stmt)
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found"
        )

    await session.delete(alert)
    await session.commit()

    return None
