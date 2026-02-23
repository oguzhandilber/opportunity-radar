"""Demand Check API endpoints."""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_context
from app.models.app_store import DemandCheckRequest, UserProfile
from app.services.demand_checker import get_demand_checker_service
from app.services.elevenlabs_service import get_elevenlabs_service

router = APIRouter()


class DemandCheckCreate(BaseModel):
    """Request model for creating a demand check."""

    business_idea: str = Field(..., min_length=10, max_length=5000)
    phone_number: Optional[str] = Field(None, description="Phone number for callback (E.164 format)")
    notify_on_high_demand: bool = Field(True, description="Call user if demand is high")


class DemandCheckResponse(BaseModel):
    """Response model for a demand check request."""

    id: int
    user_id: int
    business_idea: str
    status: str
    demand_score: Optional[float]
    analysis_text: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class DemandCheckHistoryItem(BaseModel):
    """Item in demand check history."""

    id: int
    business_idea: str
    status: str
    demand_score: Optional[float]
    created_at: datetime
    completed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


@router.post("", response_model=DemandCheckResponse)
async def create_demand_check(
    request: DemandCheckCreate,
    user_id: int = Query(1, description="User ID (for now, hardcoded)"),
):
    """
    Create a new demand check request.
    
    Submits a business idea for AI-powered market demand analysis.
    """
    async with get_db_context() as session:
        # Create the demand check request
        demand_check = DemandCheckRequest(
            user_id=user_id,
            business_idea=request.business_idea,
            status="pending",
        )
        session.add(demand_check)
        await session.commit()
        await session.refresh(demand_check)

        # Run the demand check asynchronously (in a real app, this would be a background job)
        try:
            demand_checker = get_demand_checker_service()
            result = await demand_checker.check_demand(
                business_idea=request.business_idea,
                user_id=user_id
            )
            
            # Update the demand check with results
            demand_check.status = "completed"
            demand_check.demand_score = result["demand_score"]
            demand_check.analysis_text = result["analysis_text"]
            demand_check.completed_at = datetime.utcnow()
            
            await session.commit()
            await session.refresh(demand_check)
            
            # If high demand and phone number provided, make the call
            if (request.notify_on_high_demand and 
                request.phone_number and 
                result["demand_score"] >= 70):
                
                # Trigger the call (in background)
                elevenlabs = get_elevenlabs_service()
                await elevenlabs.make_call(
                    phone_number=request.phone_number,
                    message=f"Great news! Your business idea '{request.business_idea[:50]}...' has been analyzed with a high demand score of {result['demand_score']}. Check the app for full details!",
                    user_id=user_id,
                    demand_check_id=demand_check.id
                )
                
        except Exception as e:
            # Mark as failed
            demand_check.status = "failed"
            demand_check.analysis_text = f"Error during analysis: {str(e)}"
            await session.commit()

        return demand_check


@router.get("/{demand_check_id}", response_model=DemandCheckResponse)
async def get_demand_check(
    demand_check_id: int,
    user_id: int = Query(1, description="User ID"),
):
    """Get a specific demand check request by ID."""
    async with get_db_context() as session:
        result = await session.execute(
            select(DemandCheckRequest).where(
                DemandCheckRequest.id == demand_check_id,
                DemandCheckRequest.user_id == user_id
            )
        )
        demand_check = result.scalar_one_or_none()
        
        if not demand_check:
            raise HTTPException(status_code=404, detail="Demand check not found")
        
        return demand_check


@router.get("/history", response_model=List[DemandCheckHistoryItem])
async def get_demand_check_history(
    user_id: int = Query(1, description="User ID"),
    limit: int = Query(10, ge=1, le=100, description="Number of results to return"),
):
    """Get demand check history for a user."""
    async with get_db_context() as session:
        result = await session.execute(
            select(DemandCheckRequest)
            .where(DemandCheckRequest.user_id == user_id)
            .order_by(DemandCheckRequest.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
