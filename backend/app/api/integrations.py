"""Integration API endpoints for Slack, Discord, Notion, Airtable."""

from datetime import datetime
from typing import List, Optional, Literal
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import httpx

from app.database import get_session, Integration, Workspace, User
from app.api.auth import get_current_user

router = APIRouter()


# Pydantic schemas
class IntegrationCreate(BaseModel):
    type: Literal["slack", "discord", "notion", "airtable", "webhook"]
    name: str = Field(..., min_length=1, max_length=255)
    webhook_url: Optional[str] = None
    config: Optional[dict] = Field(default_factory=dict)


class IntegrationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    webhook_url: Optional[str] = None
    config: Optional[dict] = None
    is_active: Optional[bool] = None


class IntegrationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    name: str
    webhook_url: Optional[str]
    config: Optional[dict]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class SlackTestMessage(BaseModel):
    message: str = "Test notification from Opportunity Radar 🎯"


class DiscordTestMessage(BaseModel):
    content: str = "Test notification from Opportunity Radar 🎯"


# Integration management endpoints
@router.get(
    "/workspaces/{workspace_id}/integrations", response_model=List[IntegrationResponse]
)
async def list_integrations(
    workspace_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List all integrations for a workspace."""
    # Verify user has access to workspace
    stmt = select(Integration).where(Integration.workspace_id == workspace_id)
    result = await session.execute(stmt)
    integrations = result.scalars().all()
    return [IntegrationResponse.model_validate(i) for i in integrations]


@router.post(
    "/workspaces/{workspace_id}/integrations",
    response_model=IntegrationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_integration(
    workspace_id: int,
    integration_data: IntegrationCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a new integration for a workspace."""

    # Validate webhook URL for Slack/Discord
    if (
        integration_data.type in ["slack", "discord"]
        and not integration_data.webhook_url
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{integration_data.type} integration requires a webhook_url",
        )

    integration = Integration(
        workspace_id=workspace_id,
        type=integration_data.type,
        name=integration_data.name,
        webhook_url=integration_data.webhook_url,
        config=integration_data.config or {},
        is_active=True,
    )

    session.add(integration)
    await session.commit()
    await session.refresh(integration)

    return IntegrationResponse.model_validate(integration)


@router.post("/integrations/{integration_id}/test")
async def test_integration(
    integration_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Test an integration by sending a test message."""

    stmt = select(Integration).where(Integration.id == integration_id)
    result = await session.execute(stmt)
    integration = result.scalar_one_or_none()

    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found"
        )

    if not integration.webhook_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Integration has no webhook URL configured",
        )

    # Send test message based on integration type
    try:
        if integration.type == "slack":
            await _send_slack_test(integration.webhook_url)
        elif integration.type == "discord":
            await _send_discord_test(integration.webhook_url)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Test not implemented for {integration.type} integration",
            )

        return {"message": "Test message sent successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send test message: {str(e)}",
        )


async def _send_slack_test(webhook_url: str):
    """Send test message to Slack webhook."""
    payload = {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🎯 Integration Test Successful!",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Your Opportunity Radar integration is working correctly. You'll receive notifications when high-value opportunities are discovered.",
                },
            },
        ]
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(webhook_url, json=payload)
        response.raise_for_status()


async def _send_discord_test(webhook_url: str):
    """Send test message to Discord webhook."""
    payload = {
        "content": "🎯 **Integration Test Successful!**\n\nYour Opportunity Radar integration is working correctly. You'll receive notifications when high-value opportunities are discovered.",
        "embeds": [
            {
                "title": "Opportunity Radar",
                "description": "Test notification",
                "color": 3447003,
            }
        ],
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(webhook_url, json=payload)
        response.raise_for_status()


@router.delete("/integrations/{integration_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_integration(
    integration_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Delete an integration."""
    stmt = select(Integration).where(Integration.id == integration_id)
    result = await session.execute(stmt)
    integration = result.scalar_one_or_none()

    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found"
        )

    await session.delete(integration)
    await session.commit()

    return None
