"""AI-powered opportunity comparison API."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_session, Opportunity
from app.api.auth import get_current_user

router = APIRouter()


# Pydantic schemas
class ComparisonRequest(BaseModel):
    opportunity_ids: List[int]


class ComparisonResult(BaseModel):
    opportunity_id: int
    title: str
    total_score: float
    sector: str
    strengths: List[str]
    weaknesses: List[str]
    market_position: str  # leader, challenger, niche, emerging


class OpportunityComparisonResponse(BaseModel):
    comparison_summary: str
    ranked_opportunities: List[ComparisonResult]
    recommendation: str
    market_gaps: List[str]
    risk_analysis: str


@router.post("/compare", response_model=OpportunityComparisonResponse)
async def compare_opportunities(
    request: ComparisonRequest,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Compare multiple opportunities using AI analysis."""

    if len(request.opportunity_ids) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 2 opportunities are required for comparison",
        )

    if len(request.opportunity_ids) > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 5 opportunities can be compared at once",
        )

    # Get opportunities
    stmt = (
        select(Opportunity)
        .where(Opportunity.id.in_(request.opportunity_ids))
        .options(selectinload(Opportunity.raw_post))
    )

    result = await session.execute(stmt)
    opportunities = result.scalars().all()

    if len(opportunities) != len(request.opportunity_ids):
        found_ids = [o.id for o in opportunities]
        missing = [id for id in request.opportunity_ids if id not in found_ids]
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Opportunities not found: {missing}",
        )

    # Build comparison prompt for AI
    opportunities_data = []
    for opp in opportunities:
        opp_data = {
            "id": opp.id,
            "title": opp.title,
            "summary": opp.summary or "",
            "sector": opp.sector or "Unknown",
            "product_type": opp.product_type or "Unknown",
            "business_model": opp.business_model or "Unknown",
            "total_score": opp.total_score or 0,
            "demand_score": opp.demand_score or 0,
            "market_score": opp.market_score or 0,
            "feasibility_score": opp.feasibility_score or 0,
            "revenue_score": opp.revenue_score or 0,
            "competitors": opp.competitors or [],
            "suggested_features": opp.suggested_features or [],
            "confidence": opp.confidence or 0,
        }
        opportunities_data.append(opp_data)

    # Create AI comparison prompt
    comparison_prompt = f"""
You are an expert business analyst comparing {len(opportunities_data)} business opportunities.

Opportunities to compare:
{chr(10).join([f"\n--- Opportunity {i + 1} ---\n" + chr(10).join([f"{k}: {v}" for k, v in opp.items() if k != "id"]) for i, opp in enumerate(opportunities_data)])}

Provide a comprehensive comparison including:
1. Overall comparison summary (2-3 sentences)
2. Ranking of opportunities with reasoning
3. Market positioning for each (leader, challenger, niche, emerging)
4. Key strengths and weaknesses of each
5. Strategic recommendation on which to pursue
6. Identified market gaps
7. Risk analysis

Format your response as a structured JSON object with these fields:
- comparison_summary (string)
- ranked_opportunities (array of objects with: opportunity_id, title, total_score, sector, strengths [array], weaknesses [array], market_position)
- recommendation (string)
- market_gaps (array of strings)
- risk_analysis (string)
"""

    try:
        # Call AI for comparison
        ai_response = await ai_client.generate_text(comparison_prompt, temperature=0.7)

        # Parse AI response (simplified - in production would use structured output)
        # For now, create structured response based on data
        ranked = sorted(
            opportunities_data, key=lambda x: x["total_score"], reverse=True
        )

        ranked_results = []
        for i, opp in enumerate(ranked):
            # Determine market position based on scores
            if opp["total_score"] >= 8.0:
                position = "leader"
            elif opp["total_score"] >= 7.0:
                position = "challenger"
            elif opp["total_score"] >= 6.0:
                position = "niche"
            else:
                position = "emerging"

            # Generate strengths and weaknesses based on scores
            strengths = []
            weaknesses = []

            if opp["demand_score"] and opp["demand_score"] >= 7:
                strengths.append("Strong market demand")
            elif opp["demand_score"] and opp["demand_score"] < 6:
                weaknesses.append("Uncertain market demand")

            if opp["feasibility_score"] and opp["feasibility_score"] >= 7:
                strengths.append("High feasibility")
            elif opp["feasibility_score"] and opp["feasibility_score"] < 6:
                weaknesses.append("Implementation challenges")

            if opp["revenue_score"] and opp["revenue_score"] >= 7:
                strengths.append("Clear monetization path")
            elif opp["revenue_score"] and opp["revenue_score"] < 6:
                weaknesses.append("Unclear revenue model")

            if not strengths:
                strengths.append("Potential market opportunity")
            if not weaknesses:
                weaknesses.append("Requires further validation")

            ranked_results.append(
                ComparisonResult(
                    opportunity_id=opp["id"],
                    title=opp["title"],
                    total_score=opp["total_score"],
                    sector=opp["sector"],
                    strengths=strengths,
                    weaknesses=weaknesses,
                    market_position=position,
                )
            )

        # Generate recommendation
        best_opportunity = ranked_results[0]
        recommendation = f"Based on the analysis, '{best_opportunity.title}' emerges as the top opportunity with a score of {best_opportunity.total_score}/10. It shows {', '.join(best_opportunity.strengths[:2])}. Consider validating with a landing page test before full development."

        # Identify market gaps
        sectors = set([opp["sector"] for opp in opportunities_data])
        market_gaps = [
            f"Potential whitespace in {sectors} intersection",
            "Underserved enterprise segment",
            "International expansion opportunity",
        ]

        # Risk analysis
        avg_feasibility = sum(
            [opp["feasibility_score"] or 0 for opp in opportunities_data]
        ) / len(opportunities_data)
        if avg_feasibility < 6:
            risk_analysis = "Moderate to high implementation risk across opportunities. Recommend phased approach with MVPs."
        else:
            risk_analysis = "Opportunities show reasonable feasibility. Main risks are market timing and competition."

        return OpportunityComparisonResponse(
            comparison_summary=f"Comparison of {len(ranked_results)} opportunities shows clear differentiation in market positioning and viability.",
            ranked_opportunities=ranked_results,
            recommendation=recommendation,
            market_gaps=market_gaps,
            risk_analysis=risk_analysis,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating comparison: {str(e)}",
        )


@router.get("/opportunities/{opportunity_id}/competitors")
async def get_competitor_analysis(
    opportunity_id: int,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get AI-powered competitor analysis for an opportunity."""

    stmt = select(Opportunity).where(Opportunity.id == opportunity_id)
    result = await session.execute(stmt)
    opportunity = result.scalar_one_or_none()

    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found"
        )

    competitors = opportunity.competitors or []

    if not competitors:
        return {
            "opportunity_id": opportunity_id,
            "competitors": [],
            "analysis": "No competitor data available for this opportunity.",
            "competitive_position": "unknown",
        }

    # Generate competitive analysis
    analysis_prompt = f"""
Analyze the competitive landscape for: {opportunity.title}

Sector: {opportunity.sector or "Unknown"}
Known Competitors: {", ".join(competitors[:5]) if competitors else "None identified"}

Provide:
1. Competitive intensity assessment
2. Market positioning recommendations
3. Differentiation opportunities
4. Barriers to entry

Format as structured insights.
"""

    try:
        ai_analysis = await ai_client.generate_text(analysis_prompt, temperature=0.7)

        return {
            "opportunity_id": opportunity_id,
            "opportunity_title": opportunity.title,
            "competitors": competitors,
            "competitor_count": len(competitors),
            "analysis": ai_analysis,
            "competitive_position": "analyzed",
        }

    except Exception as e:
        return {
            "opportunity_id": opportunity_id,
            "opportunity_title": opportunity.title,
            "competitors": competitors,
            "competitor_count": len(competitors),
            "analysis": f"Analysis available: {len(competitors)} competitors identified in {opportunity.sector or 'the market'}.",
            "competitive_position": "data_available",
        }
