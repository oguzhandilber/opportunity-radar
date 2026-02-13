"""Opportunity classifier using AI."""

import logging

from app.analyzers.ai_client import get_ai_client

logger = logging.getLogger(__name__)

CLASSIFICATION_PROMPT = """Analyze this content and extract business opportunity information.

Content:
{content}

Provide a JSON response with:
{{
    "is_opportunity": true/false,
    "title": "Short descriptive title for the opportunity",
    "summary": "2-3 sentence summary of the opportunity",
    "product_type": "SaaS|Mobile App|Chrome Extension|API|Telegram Bot|AI Agent|Other",
    "sector": "Fintech|Health|Education|Productivity|E-commerce|Marketing|HR|Other",
    "business_model": "Subscription|Freemium|One-time|Transaction fee|Advertising|Other"
}}

If this is not a valid business opportunity, set is_opportunity to false and leave other fields as null.
Only respond with JSON, no other text."""


class OpportunityClassifier:
    """Classify opportunities using AI."""

    def __init__(self):
        self.client = get_ai_client()

    async def classify(self, content: str) -> dict | None:
        """Classify content as a business opportunity."""
        try:
            prompt = CLASSIFICATION_PROMPT.format(content=content[:3000])
            result = await self.client.complete_json(prompt)

            if not result.get("is_opportunity"):
                return None

            return {
                "title": result.get("title"),
                "summary": result.get("summary"),
                "product_type": result.get("product_type"),
                "sector": result.get("sector"),
                "business_model": result.get("business_model"),
            }

        except Exception as e:
            logger.error(f"Classification error: {e}")
            return None
