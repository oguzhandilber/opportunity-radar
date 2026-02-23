"""AI Demand Checker Service.

Analyzes market demand for a business idea using AI and existing market data.
"""

import logging
from typing import Any, Dict, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.analyzers.ai_client import get_ai_client
from app.database import get_db_context
from app.models.app_store import (
    AppStoreApp,
    AppStoreCategory,
    AppScore,
    CATEGORY_REVENUE_BENCHMARKS,
)

logger = logging.getLogger(__name__)


class DemandCheckerService:
    """AI-powered service to check market demand for business ideas."""

    def __init__(self):
        self.ai_client = get_ai_client()

    async def check_demand(
        self, business_idea: str, user_id: int
    ) -> Dict[str, Any]:
        """
        Analyze market demand for a business idea.
        
        Args:
            business_idea: Description of the business idea
            user_id: ID of the user making the request
            
        Returns:
            Dict with demand_score (0-100) and analysis_text
        """
        # Get relevant market data from existing apps
        market_data = await self._get_market_data(business_idea)
        
        # Use AI to analyze demand
        analysis = await self._analyze_demand(business_idea, market_data)
        
        return analysis

    async def _get_market_data(self, business_idea: str) -> Dict[str, Any]:
        """Get relevant market data based on the business idea."""
        async with get_db_context() as session:
            # Get top categories
            categories = await session.execute(
                select(AppStoreCategory).order_by(AppStoreCategory.app_count.desc()).limit(5)
            )
            categories = categories.scalars().all()
            
            # Get apps that might be relevant (based on high scores)
            apps = await session.execute(
                select(AppStoreApp)
                .join(AppScore, AppScore.app_id == AppStoreApp.id)
                .order_by(AppScore.total_opportunity_score.desc())
                .limit(10)
            )
            apps = apps.scalars().all()
            
            return {
                "categories": [
                    {"name": c.name, "app_count": c.app_count, "revenue_benchmark": c.revenue_benchmark}
                    for c in categories
                ],
                "top_apps": [
                    {
                        "name": a.name,
                        "category": a.category.name if a.category else "Unknown",
                        "rating": a.rating,
                        "download_estimate": a.download_estimate,
                    }
                    for a in apps
                    if a.category
                ],
            }

    async def _analyze_demand(
        self, business_idea: str, market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Use AI to analyze demand for the business idea."""
        
        # Build context from market data
        categories_info = "\n".join([
            f"- {c['name']}: {c['app_count']} apps, ${c['revenue_benchmark']}/1000 downloads"
            for c in market_data.get("categories", [])
        ])
        
        top_apps_info = "\n".join([
            f"- {a['name']} ({a['category']}): {a['rating']} rating, ~{a['download_estimate']} downloads"
            for a in market_data.get("top_apps", [])[:5]
        ])
        
        system_prompt = """You are a market demand analyst. Analyze the given business idea and provide:
1. A demand_score from 0-100 (100 = very high demand)
2. A brief analysis_text explaining your reasoning

Consider:
- Is there existing competition?
- Is the market growing?
- Is there user pain point being addressed?
- Revenue potential

Return JSON with exactly: {"demand_score": <number>, "analysis_text": "<explanation>"}"""

        user_prompt = f"""Analyze market demand for this business idea:

Business Idea: {business_idea}

Market Context:
Top Categories:
{categories_info}

Top Performing Apps:
{top_apps_info}

Provide your analysis as JSON."""

        try:
            result = await self.ai_client.complete_json(user_prompt, system_prompt)
            
            # Ensure we have valid scores
            demand_score = result.get("demand_score", 50)
            demand_score = max(0, min(100, float(demand_score)))  # Clamp to 0-100
            
            analysis_text = result.get("analysis_text") or "Analysis completed."
            
            return {
                "demand_score": demand_score,
                "analysis_text": analysis_text,
            }
        except Exception as e:
            logger.error(f"Error in AI demand analysis: {e}")
            return {
                "demand_score": 50,  # Default middle score on error
                "analysis_text": f"Analysis completed with limited data. Error: {str(e)}",
            }


# Singleton instance
_demand_checker_service: Optional[DemandCheckerService] = None


def get_demand_checker_service() -> DemandCheckerService:
    """Get the singleton demand checker service instance."""
    global _demand_checker_service
    if _demand_checker_service is None:
        _demand_checker_service = DemandCheckerService()
    return _demand_checker_service
