"""Opportunity scorer using AI."""

import logging

from app.analyzers.ai_client import get_ai_client

logger = logging.getLogger(__name__)

SCORING_PROMPT = """Score this business opportunity on multiple dimensions.

Opportunity:
Title: {title}
Summary: {summary}
Product Type: {product_type}
Sector: {sector}
Business Model: {business_model}

Original Content:
{content}

Score each dimension from 1-10 and provide confidence level:

1. Demand Score (1-10): How strong are the demand signals?
   - Explicit requests, pain intensity, frequency, willingness to pay

2. Market Score (1-10): How good is the market potential?
   - Market size, growth trend, competition level, Turkey fit

3. Feasibility Score (1-10): How feasible is this to build?
   - Technical complexity, time to MVP, solo developer fit, regulatory risk

4. Revenue Score (1-10): How good is the revenue potential?
   - Monetization clarity, pricing benchmark, LTV estimate, CAC estimate

Respond with JSON only:
{{
    "demand_score": 1-10,
    "market_score": 1-10,
    "feasibility_score": 1-10,
    "revenue_score": 1-10,
    "total_score": (weighted average),
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation of scores"
}}"""


class OpportunityScorer:
    """Score opportunities using AI."""

    def __init__(self):
        self.client = get_ai_client()

    async def score(self, content: str, classification: dict | None) -> dict:
        """Score an opportunity on multiple dimensions."""
        if classification is None:
            classification = {}

        try:
            prompt = SCORING_PROMPT.format(
                title=classification.get("title", "Unknown"),
                summary=classification.get("summary", ""),
                product_type=classification.get("product_type", "Unknown"),
                sector=classification.get("sector", "Unknown"),
                business_model=classification.get("business_model", "Unknown"),
                content=content[:2000],
            )

            result = await self.client.complete_json(prompt)

            # Calculate total score if not provided
            if "total_score" not in result or result["total_score"] is None:
                scores = [
                    result.get("demand_score", 5),
                    result.get("market_score", 5),
                    result.get("feasibility_score", 5),
                    result.get("revenue_score", 5),
                ]
                # Weighted average: demand and feasibility weighted higher
                weights = [1.5, 1.0, 1.5, 1.0]
                result["total_score"] = sum(
                    s * w for s, w in zip(scores, weights)
                ) / sum(weights)

            return {
                "demand_score": result.get("demand_score"),
                "market_score": result.get("market_score"),
                "feasibility_score": result.get("feasibility_score"),
                "revenue_score": result.get("revenue_score"),
                "total_score": round(result.get("total_score", 5), 2),
                "confidence": result.get("confidence", 0.5),
            }

        except Exception as e:
            logger.error(f"Scoring error: {e}")
            return {
                "demand_score": 5,
                "market_score": 5,
                "feasibility_score": 5,
                "revenue_score": 5,
                "total_score": 5,
                "confidence": 0.3,
            }
