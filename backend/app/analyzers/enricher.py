"""Opportunity enricher using AI."""

import logging

from app.analyzers.ai_client import get_ai_client

logger = logging.getLogger(__name__)

ENRICHMENT_PROMPT = """Enrich this business opportunity with additional insights.

Opportunity:
Title: {title}
Summary: {summary}
Product Type: {product_type}
Sector: {sector}
Business Model: {business_model}

Original Content:
{content}

Provide enrichment data:

1. Competitors: List 3-5 existing solutions or competitors (with URLs if known)
2. Suggested Features: List 5-7 key features for an MVP
3. Go-to-Market: Brief go-to-market strategy (2-3 paragraphs)

Focus on the Turkish market where applicable.

Respond with JSON only:
{{
    "competitors": [
        {{"name": "Competitor Name", "url": "https://...", "notes": "Brief description"}}
    ],
    "suggested_features": [
        {{"feature": "Feature name", "priority": "high|medium|low", "description": "Brief description"}}
    ],
    "go_to_market": "Go-to-market strategy text..."
}}"""


class OpportunityEnricher:
    """Enrich opportunities with additional insights using AI."""

    def __init__(self):
        self.client = get_ai_client()

    async def enrich(self, content: str, classification: dict | None) -> dict:
        """Enrich an opportunity with competitors, features, and GTM strategy."""
        if classification is None:
            classification = {}

        try:
            prompt = ENRICHMENT_PROMPT.format(
                title=classification.get("title", "Unknown"),
                summary=classification.get("summary", ""),
                product_type=classification.get("product_type", "Unknown"),
                sector=classification.get("sector", "Unknown"),
                business_model=classification.get("business_model", "Unknown"),
                content=content[:2000],
            )

            result = await self.client.complete_json(prompt)

            return {
                "competitors": result.get("competitors", []),
                "suggested_features": result.get("suggested_features", []),
                "go_to_market": result.get("go_to_market", ""),
            }

        except Exception as e:
            logger.error(f"Enrichment error: {e}")
            return {
                "competitors": [],
                "suggested_features": [],
                "go_to_market": "",
            }
