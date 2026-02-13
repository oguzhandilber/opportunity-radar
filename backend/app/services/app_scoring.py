"""App Store AI Scoring Service.

Scores apps based on:
- Build Ease Score: Technical complexity, MVP time
- Revenue Potential Score: Market size, pricing, monetization
- Market Opportunity Score: Competition, growth, pain points
- Rising Score: Momentum, velocity, trends
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analyzers.ai_client import get_ai_client
from app.database import get_db_context
from app.models.app_store import (
    AppStoreApp,
    AppScore,
    AppTrendHistory,
    CATEGORY_REVENUE_BENCHMARKS,
    CATEGORY_COMPLEXITY,
)
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Complexity indicators in app descriptions
COMPLEXITY_KEYWORDS = {
    "high": [
        "machine learning",
        "ai",
        "neural",
        "ar",
        "augmented reality",
        "vr",
        "virtual reality",
        "blockchain",
        "crypto",
        "websocket",
        "real-time",
        "video",
        "streaming",
        "3d",
        "games engine",
    ],
    "medium": [
        "api",
        "database",
        "auth",
        "payment",
        "social login",
        "push notifications",
        "offline",
        "sync",
        "maps",
        "location",
        "camera",
        "bluetooth",
        "healthkit",
        "healthkit",
    ],
    "simple": [
        "todo",
        "notes",
        "calculator",
        "timer",
        "flashlight",
        "simple",
        "basic",
        "checklist",
        "reminder",
    ],
}

# Revenue opportunity keywords
REVENUE_KEYWORDS = {
    "high": [
        "business",
        "finance",
        "invest",
        "trading",
        "crypto",
        "enterprise",
        "professional",
        "subscription",
        "saas",
        "b2b",
        "payment",
        "banking",
        "money",
    ],
    "medium": [
        "productivity",
        "health",
        "fitness",
        "education",
        "medical",
        "lifestyle",
        "food",
        "recipe",
        "shopping",
    ],
    "low": [
        "entertainment",
        "games",
        "fun",
        "social",
        "free",
        "casual",
        "simple",
        "basic",
    ],
}

# Growth indicators
GROWTH_KEYWORDS = {
    "positive": [
        "growing",
        "trending",
        "viral",
        "explosive",
        "rising",
        "demand",
        "popular",
        "hit",
        "buzz",
        "momentum",
    ],
    "negative": [
        "saturated",
        "declining",
        "dying",
        "old",
        "outdated",
        "legacy",
        "niche",
        "declining",
    ],
}


class AppScoringService:
    """AI-powered scoring service for App Store opportunities."""

    def __init__(self):
        self.ai_client = get_ai_client()

    async def score_app(self, app_id: int) -> Optional[AppScore]:
        """Score a single app and store results."""
        async with get_db_context() as session:
            # Fetch app with category
            app = await self._get_app_with_details(session, app_id)
            if not app:
                logger.warning(f"App {app_id} not found")
                return None

            # Calculate scores
            build_ease = await self._score_build_ease(app)
            revenue = await self._score_revenue_potential(app)
            market = await self._score_market_opportunity(app)
            rising = await self._score_rising_potential(app)

            # Calculate total score (weighted)
            total = self._calculate_total_score(build_ease, revenue, market, rising)

            # AI analysis
            analysis = await self._generate_ai_analysis(
                app, build_ease, revenue, market, rising
            )

            # Create or update score
            score = await self._upsert_score(
                session,
                app_id,
                {
                    "build_ease_score": build_ease["score"],
                    "revenue_potential_score": revenue["score"],
                    "market_opportunity_score": market["score"],
                    "rising_score": rising["score"],
                    "total_opportunity_score": total,
                    "build_ease_factors": build_ease["factors"],
                    "revenue_factors": revenue["factors"],
                    "market_factors": market["factors"],
                    "rising_factors": rising["factors"],
                    "confidence_score": analysis["confidence"],
                    "analysis_text": analysis["text"],
                    "opportunity_summary": analysis["summary"],
                },
            )

            return score

    async def _score_build_ease(self, app: AppStoreApp) -> Dict[str, Any]:
        """Score build ease based on technical complexity."""
        factors = {}
        score = 50.0  # Start at middle

        # Category complexity (from benchmarks)
        category = app.category
        if category:
            complexity = category.complexity_multiplier or 0.5
            score -= complexity * 30  # Reduce by up to 30 points
            factors["category_complexity"] = complexity

        # Price indicator (paid apps often more complex)
        if app.price and app.price > 20:
            score += 5
            factors["price_indicator"] = "premium"
        elif app.price and app.price == 0:
            score -= 3
            factors["price_indicator"] = "free"

        # Description complexity analysis
        description = app.description or ""
        desc_lower = description.lower()

        # Check for complex keywords
        for keyword in COMPLEXITY_KEYWORDS.get("high", []):
            if keyword in desc_lower:
                score -= 10
                factors[f"complex_{keyword}"] = True

        for keyword in COMPLEXITY_KEYWORDS.get("simple", []):
            if keyword in desc_lower:
                score += 8
                factors[f"simple_{keyword}"] = True

        # Age factor (newer apps might be more complex)
        if app.age_in_days and app.age_in_days < 30:
            score -= 5
            factors["recent_release"] = True

        # Rating correlation (higher rating often = simpler but polished)
        if app.rating and app.rating >= 4.5:
            score += 3
            factors["high_quality"] = True

        # Clamp score
        score = max(0, min(100, score))
        factors["raw_score"] = score

        return {"score": round(score, 1), "factors": factors}

    async def _score_revenue_potential(self, app: AppStoreApp) -> Dict[str, Any]:
        """Score revenue potential based on market and pricing."""
        factors = {}
        score = 50.0

        # Category revenue benchmark
        category = app.category
        if category:
            benchmark = category.revenue_benchmark or 20.0
            # Normalize to 0-100 (benchmark 100+ = 100)
            normalized_benchmark = min(100, benchmark)
            score += (normalized_benchmark - 50) * 0.5
            factors["category_benchmark"] = benchmark

        # Price point
        if app.price:
            if app.price > 50:
                score += 10  # Premium pricing power
                factors["premium_pricing"] = True
            elif app.price > 10:
                score += 5
            elif app.price == 0:
                score -= 5
                factors["free_app"] = True

        # Rating indicates willingness to pay
        if app.rating:
            if app.rating >= 4.5:
                score += 5
                factors["high_satisfaction"] = True
            elif app.rating < 3.5:
                score -= 10
                factors["low_satisfaction"] = True

        # Rating count (more reviews = bigger market)
        if app.rating_count:
            if app.rating_count > 100000:
                score += 15
                factors["large_user_base"] = True
            elif app.rating_count > 10000:
                score += 8
            elif app.rating_count > 1000:
                score += 3

        # Recent ratings velocity
        if app.current_rating_count and app.rating_count:
            velocity = app.current_rating_count / max(1, app.rating_count)
            if velocity > 0.1:  # >10% recent ratings
                score += 5
                factors["active_growth"] = True

        # Clamp score
        score = max(0, min(100, score))
        factors["raw_score"] = round(score, 1)

        return {"score": round(score, 1), "factors": factors}

    async def _score_market_opportunity(self, app: AppStoreApp) -> Dict[str, Any]:
        """Score market opportunity based on competition and growth."""
        factors = {}
        score = 50.0

        # Category growth indicators from description
        description = app.description or ""
        desc_lower = description.lower()

        # Growth keywords
        for keyword in GROWTH_KEYWORDS.get("positive", []):
            if keyword in desc_lower:
                score += 3
                factors[f"growth_{keyword}"] = True

        for keyword in GROWTH_KEYWORDS.get("negative", []):
            if keyword in desc_lower:
                score -= 5
                factors[f"decline_{keyword}"] = True

        # Competition proxy (rating count = competition)
        if app.rating_count:
            if app.rating_count > 500000:
                score -= 15  # Very competitive
                factors["high_competition"] = True
            elif app.rating_count > 100000:
                score -= 8
            elif app.rating_count < 1000:
                score += 10  # Low competition opportunity
                factors["low_competition"] = True

        # Age - newer markets might be underserved
        if app.age_in_days:
            if app.age_in_days < 180:  # Less than 6 months
                score += 8
                factors["emerging_market"] = True
            elif app.age_in_days > 1825:  # More than 5 years
                score -= 5
                factors["mature_market"] = True

        # Rating quality
        if app.rating and app.rating >= 4.0:
            if app.rating_count and app.rating_count < 50000:
                score += 5  # High quality with less competition
                factors["quality_gap"] = True

        # Clamp score
        score = max(0, min(100, score))
        factors["raw_score"] = round(score, 1)

        return {"score": round(score, 1), "factors": factors}

    async def _score_rising_potential(self, app: AppStoreApp) -> Dict[str, Any]:
        """Score rising potential based on momentum."""
        factors = {}
        score = 50.0

        # New release indicator
        if app.is_new_release:
            score += 15
            factors["new_release"] = True

        # Already flagged as rising
        if app.is_rising:
            score += 20
            factors["flagged_rising"] = True

        # Trend direction
        if app.trend_direction == "up":
            score += 15
            factors["trend_up"] = True
        elif app.trend_direction == "down":
            score -= 10
            factors["trend_down"] = True

        # Engagement score
        if app.engagement_score:
            if app.engagement_score > 70:
                score += 10
                factors["high_engagement"] = True
            elif app.engagement_score < 30:
                score -= 5
                factors["low_engagement"] = True

        # Age factor - newer apps with momentum
        if app.age_in_days:
            if app.age_in_days < 30:
                score += 10  # Fresh apps with room to grow
                factors["fresh_app"] = True
            elif app.age_in_days > 3650:  # 10+ years
                score -= 15  # Old app, less rising potential
                factors["legacy_app"] = True

        # Active user estimate
        if app.active_user_estimate and app.download_estimate:
            ratio = app.active_user_estimate / app.download_estimate
            if ratio > 0.5:
                score += 8
                factors["good_retention"] = True

        # Clamp score
        score = max(0, min(100, score))
        factors["raw_score"] = round(score, 1)

        return {"score": round(score, 1), "factors": factors}

    def _calculate_total_score(
        self, build_ease: Dict, revenue: Dict, market: Dict, rising: Dict
    ) -> float:
        """Calculate weighted total opportunity score."""
        weights = {
            "revenue": 0.35,  # Revenue is most important
            "market": 0.25,
            "rising": 0.25,
            "build_ease": 0.15,
        }

        total = (
            revenue["score"] * weights["revenue"]
            + market["score"] * weights["market"]
            + rising["score"] * weights["rising"]
            + build_ease["score"] * weights["build_ease"]
        )

        return round(total, 1)

    async def _generate_ai_analysis(
        self,
        app: AppStoreApp,
        build_ease: Dict,
        revenue: Dict,
        market: Dict,
        rising: Dict,
    ) -> Dict[str, Any]:
        """Generate AI analysis summary."""
        prompt = f"""
Analyze this App Store opportunity:

App: {app.name}
Developer: {app.developer}
Category: {app.category.name if app.category else "Unknown"}
Rating: {app.rating} ({app.rating_count} reviews)
Price: ${app.price}

Build Ease Score: {build_ease["score"]}/100
Revenue Potential: {revenue["score"]}/100
Market Opportunity: {market["score"]}/100
Rising Score: {rising["score"]}/100

Provide a brief analysis (2-3 sentences) about:
1. Is this a good opportunity to clone/iterate on?
2. What makes it attractive (or not)?
3. Any red flags?

Respond with JSON:
{{
    "analysis": "Your 2-3 sentence analysis",
    "confidence": 0.0-1.0,
    "summary": "One sentence opportunity summary"
}}
"""

        try:
            result = await self.ai_client.complete_json(prompt)
            return {
                "text": result.get("analysis", ""),
                "confidence": result.get("confidence", 0.7),
                "summary": result.get("summary", ""),
            }
        except Exception as e:
            logger.error(f"AI analysis error: {e}")
            return {
                "text": "Analysis unavailable due to AI service error.",
                "confidence": 0.5,
                "summary": f"Potential opportunity in {app.category.name if app.category else 'unknown'} category.",
            }

    async def _get_app_with_details(
        self, session: AsyncSession, app_id: int
    ) -> Optional[AppStoreApp]:
        """Fetch app with category and trend data."""
        from sqlalchemy.orm import selectinload

        query = (
            select(AppStoreApp)
            .options(
                selectinload(AppStoreApp.category),
                selectinload(AppStoreApp.trend_history),
            )
            .where(AppStoreApp.id == app_id)
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def _upsert_score(
        self, session: AsyncSession, app_id: int, score_data: Dict[str, Any]
    ) -> AppScore:
        """Create or update app score."""
        query = select(AppScore).where(AppScore.app_id == app_id)
        result = await session.execute(query)
        score = result.scalar_one_or_none()

        if score:
            # Update existing
            for key, value in score_data.items():
                setattr(score, key, value)
            score.scored_at = datetime.now(timezone.utc)
        else:
            # Create new
            score = AppScore(app_id=app_id, **score_data)
            session.add(score)

        await session.commit()
        await session.refresh(score)

        return score

    async def score_all_apps(self, batch_size: int = 50) -> Dict[str, int]:
        """Score all apps in database."""
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        async with get_db_context() as session:
            query = select(AppStoreApp.id).options(selectinload(AppStoreApp.category))
            result = await session.execute(query)
            app_ids = [row[0] for row in result.fetchall()]

        scored = 0
        errors = 0

        for app_id in app_ids:
            try:
                await self.score_app(app_id)
                scored += 1
            except Exception as e:
                logger.error(f"Error scoring app {app_id}: {e}")
                errors += 1

        return {"scored": scored, "errors": errors}


async def run_scoring_service():
    """Run the scoring service for all unscored apps."""
    logger.info("Starting App Store scoring service...")
    service = AppScoringService()
    results = await service.score_all_apps()
    logger.info(f"Scoring complete: {results}")


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) > 1 and sys.argv[1] == "--score":
        asyncio.run(run_scoring_service())
