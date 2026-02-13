"""Historical Tracking Service for App Store Apps.

Captures daily metrics, calculates velocity, and determines trend directions.
Provides historical analysis for opportunity assessment.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select, and_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_context
from app.models.app_store import (
    AppStoreApp,
    AppRevenueHistory,
    AppViralHistory,
    AppTrendHistory,
    CATEGORY_REVENUE_BENCHMARKS,
)

logger = logging.getLogger(__name__)


class HistoricalTrackingService:
    """Service for tracking historical app metrics and calculating trends."""

    async def capture_daily_metrics(self) -> Dict[str, int]:
        """Capture daily metrics for all apps."""
        async with get_db_context() as session:
            # Get all apps
            query = select(AppStoreApp).where(AppStoreApp.download_estimate > 0)
            result = await session.execute(query)
            apps = result.scalars().all()

            revenue_count = 0
            viral_count = 0
            trend_count = 0
            errors = 0

            for app in apps:
                try:
                    # Calculate and store revenue metrics
                    await self._capture_revenue_metrics(session, app)
                    revenue_count += 1

                    # Store viral metrics
                    await self._capture_viral_metrics(session, app)
                    viral_count += 1

                    # Store trend metrics
                    await self._capture_trend_metrics(session, app)
                    trend_count += 1

                except Exception as e:
                    logger.error(f"Error capturing metrics for app {app.id}: {e}")
                    errors += 1

            await session.commit()

            return {
                "apps_processed": len(apps),
                "revenue_records": revenue_count,
                "viral_records": viral_count,
                "trend_records": trend_count,
                "errors": errors,
            }

    async def get_app_history(
        self, app_id: int, days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get historical data for an app."""
        async with get_db_context() as session:
            # Get date range
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days)

            # Query different history types
            revenue_query = (
                select(AppRevenueHistory)
                .where(
                    and_(
                        AppRevenueHistory.app_id == app_id,
                        AppRevenueHistory.recorded_at >= start_date,
                    )
                )
                .order_by(desc(AppRevenueHistory.recorded_at))
            )

            viral_query = (
                select(AppViralHistory)
                .where(
                    and_(
                        AppViralHistory.app_id == app_id,
                        AppViralHistory.recorded_at >= start_date,
                    )
                )
                .order_by(desc(AppViralHistory.recorded_at))
            )

            trend_query = (
                select(AppTrendHistory)
                .where(
                    and_(
                        AppTrendHistory.app_id == app_id,
                        AppTrendHistory.recorded_at >= start_date,
                    )
                )
                .order_by(desc(AppTrendHistory.recorded_at))
            )

            revenue_result = await session.execute(revenue_query)
            viral_result = await session.execute(viral_query)
            trend_result = await session.execute(trend_query)

            # Combine data by date
            history_data = {}

            # Add revenue data
            for record in revenue_result.scalars().all():
                date_key = record.recorded_at.date().isoformat()
                history_data[date_key] = {
                    "date": date_key,
                    "revenue": {
                        "monthly_estimate": record.monthly_estimate,
                        "yearly_estimate": record.yearly_estimate,
                        "confidence": record.confidence,
                        "revenue_velocity": record.revenue_velocity,
                    },
                }

            # Add viral data
            for record in viral_result.scalars().all():
                date_key = record.recorded_at.date().isoformat()
                if date_key not in history_data:
                    history_data[date_key] = {"date": date_key}
                history_data[date_key]["viral"] = {
                    "score": record.viral_score,
                    "velocity": record.velocity,
                    "coefficient": record.coefficient,
                    "signals": record.signals_detected,
                }

            # Add trend data
            for record in trend_result.scalars().all():
                date_key = record.recorded_at.date().isoformat()
                if date_key not in history_data:
                    history_data[date_key] = {"date": date_key}
                history_data[date_key]["trend"] = {
                    "rating": record.rating,
                    "rating_count": record.rating_count,
                    "rating_velocity": record.rating_velocity,
                    "ranking": record.ranking,
                    "ranking_change": record.ranking_change,
                }

            # Sort by date and return as list
            return sorted(history_data.values(), key=lambda x: x["date"], reverse=True)

    async def calculate_velocity(self, app_id: int, days: int = 7) -> Dict[str, float]:
        """Calculate growth velocity metrics."""
        async with get_db_context() as session:
            # Get historical data
            history = await self.get_app_history(app_id, days)

            if len(history) < 2:
                return {
                    "rating_velocity": 0.0,
                    "revenue_velocity": 0.0,
                    "engagement_velocity": 0.0,
                    "momentum_score": 0.0,
                }

            # Calculate velocities
            rating_velocity = self._calculate_rating_velocity(history)
            revenue_velocity = self._calculate_revenue_velocity(history)
            engagement_velocity = self._calculate_engagement_velocity(history)
            momentum_score = self._calculate_momentum_score(
                rating_velocity, revenue_velocity, engagement_velocity
            )

            return {
                "rating_velocity": round(rating_velocity, 2),
                "revenue_velocity": round(revenue_velocity, 2),
                "engagement_velocity": round(engagement_velocity, 2),
                "momentum_score": round(momentum_score, 1),
            }

    async def get_trend_direction(self, app_id: int, days: int = 30) -> str:
        """Determine trend direction: rising, falling, stable."""
        velocity_data = await self.calculate_velocity(app_id, days)

        momentum = velocity_data["momentum_score"]
        revenue_vel = velocity_data["revenue_velocity"]
        rating_vel = velocity_data["rating_velocity"]

        # Determine trend based on multiple factors
        if momentum >= 70 and revenue_vel > 5.0 and rating_vel > 1.0:
            return "rising"
        elif momentum <= 30 or (revenue_vel < -5.0 and rating_vel < -1.0):
            return "falling"
        else:
            return "stable"

    async def _capture_revenue_metrics(
        self, session: AsyncSession, app: AppStoreApp
    ) -> None:
        """Capture revenue metrics for an app."""
        # Calculate current revenue estimate
        category_name = app.category.name if app.category else "Unknown"
        revenue_per_1k = CATEGORY_REVENUE_BENCHMARKS.get(category_name, 20.0)

        monthly_estimate = int((app.download_estimate / 1000) * revenue_per_1k)
        yearly_estimate = monthly_estimate * 12

        # Calculate confidence based on data quality
        confidence = self._calculate_revenue_confidence(app)

        # Calculate velocities (comparing to last record)
        last_record_query = (
            select(AppRevenueHistory)
            .where(AppRevenueHistory.app_id == app.id)
            .order_by(desc(AppRevenueHistory.recorded_at))
            .limit(1)
        )
        last_result = await session.execute(last_record_query)
        last_record = last_result.scalar_one_or_none()

        download_velocity = 0.0
        revenue_velocity = 0.0

        if last_record:
            days_diff = (datetime.now(timezone.utc) - last_record.recorded_at).days
            if days_diff > 0:
                download_change = app.download_estimate - (
                    last_record.monthly_estimate * 1000 / revenue_per_1k
                )
                download_velocity = download_change / days_diff

                revenue_change = monthly_estimate - last_record.monthly_estimate
                revenue_velocity = (
                    (revenue_change / last_record.monthly_estimate * 100)
                    if last_record.monthly_estimate > 0
                    else 0.0
                )

        # Create new record
        revenue_record = AppRevenueHistory(
            app_id=app.id,
            monthly_estimate=monthly_estimate,
            yearly_estimate=yearly_estimate,
            confidence=confidence,
            download_velocity=download_velocity,
            revenue_velocity=revenue_velocity,
        )
        session.add(revenue_record)

    async def _capture_viral_metrics(
        self, session: AsyncSession, app: AppStoreApp
    ) -> None:
        """Capture viral metrics for an app."""
        # Use existing viral metrics from the app
        viral_score = app.viral_score or 0.0
        velocity = app.viral_velocity or 0.0
        coefficient = app.viral_coefficient or 0.0

        # Detect viral signals
        signals = []
        if viral_score > 70:
            signals.append("high_viral_score")
        if velocity > 10:
            signals.append("rapid_growth")
        if coefficient > 1.5:
            signals.append("strong_k_factor")
        if app.early_viral_signal:
            signals.append("early_signal")

        # Create new record
        viral_record = AppViralHistory(
            app_id=app.id,
            viral_score=viral_score,
            velocity=velocity,
            coefficient=coefficient,
            signals_detected=signals,
        )
        session.add(viral_record)

    async def _capture_trend_metrics(
        self, session: AsyncSession, app: AppStoreApp
    ) -> None:
        """Capture trend metrics for an app."""
        # Get last record for comparison
        last_record_query = (
            select(AppTrendHistory)
            .where(AppTrendHistory.app_id == app.id)
            .order_by(desc(AppTrendHistory.recorded_at))
            .limit(1)
        )
        last_result = await session.execute(last_record_query)
        last_record = last_result.scalar_one_or_none()

        # Calculate changes
        ranking_change = 0
        rating_change = 0.0
        rating_velocity = 0.0

        if last_record:
            rating_change = (app.rating or 0.0) - (last_record.rating or 0.0)
            ranking_change = (app.ranking or 0) - (last_record.ranking or 0)

            # Calculate rating velocity (new ratings per day)
            days_diff = (datetime.now(timezone.utc) - last_record.recorded_at).days
            if days_diff > 0 and app.rating_count and last_record.rating_count:
                new_ratings = app.rating_count - last_record.rating_count
                rating_velocity = new_ratings / days_diff

        # Create new record
        trend_record = AppTrendHistory(
            app_id=app.id,
            ranking=app.ranking,
            category_ranking=None,  # Could be calculated if needed
            rating=app.rating,
            rating_count=app.rating_count,
            rating_velocity=rating_velocity,
            ranking_change=ranking_change,
            rating_change=rating_change,
        )
        session.add(trend_record)

    def _calculate_revenue_confidence(self, app: AppStoreApp) -> float:
        """Calculate confidence score for revenue estimate."""
        confidence = 0.5  # Base confidence

        # Higher confidence for apps with more data
        if app.rating_count:
            if app.rating_count > 100000:
                confidence += 0.3
            elif app.rating_count > 10000:
                confidence += 0.2
            elif app.rating_count > 1000:
                confidence += 0.1

        # Higher confidence for paid apps
        if app.price and app.price > 0:
            confidence += 0.1

        # Higher confidence for apps with ratings
        if app.rating and app.rating >= 4.0:
            confidence += 0.1

        return min(1.0, confidence)

    def _calculate_rating_velocity(self, history: List[Dict[str, Any]]) -> float:
        """Calculate rating velocity from historical data."""
        if len(history) < 2:
            return 0.0

        recent_ratings = []
        for record in history[:7]:  # Last 7 days
            if "trend" in record and record["trend"].get("rating_velocity"):
                recent_ratings.append(record["trend"]["rating_velocity"])

        return sum(recent_ratings) / len(recent_ratings) if recent_ratings else 0.0

    def _calculate_revenue_velocity(self, history: List[Dict[str, Any]]) -> float:
        """Calculate revenue velocity from historical data."""
        if len(history) < 2:
            return 0.0

        revenue_changes = []
        for record in history[:7]:  # Last 7 days
            if "revenue" in record and record["revenue"].get("revenue_velocity"):
                revenue_changes.append(record["revenue"]["revenue_velocity"])

        return sum(revenue_changes) / len(revenue_changes) if revenue_changes else 0.0

    def _calculate_engagement_velocity(self, history: List[Dict[str, Any]]) -> float:
        """Calculate engagement velocity from viral metrics."""
        if len(history) < 2:
            return 0.0

        engagement_changes = []
        for record in history[:7]:  # Last 7 days
            if "viral" in record and record["viral"].get("velocity"):
                engagement_changes.append(record["viral"]["velocity"])

        return (
            sum(engagement_changes) / len(engagement_changes)
            if engagement_changes
            else 0.0
        )

    def _calculate_momentum_score(
        self,
        rating_velocity: float,
        revenue_velocity: float,
        engagement_velocity: float,
    ) -> float:
        """Calculate overall momentum score (0-100)."""
        # Normalize velocities to 0-100 scale
        rating_score = min(
            100, max(0, rating_velocity * 10)
        )  # 10 ratings/day = 100 points
        revenue_score = min(
            100, max(0, revenue_velocity + 50)
        )  # 50% growth = 100 points
        engagement_score = min(
            100, max(0, engagement_velocity * 5)
        )  # 20 engagement units = 100 points

        # Weighted average (revenue is most important)
        momentum = revenue_score * 0.5 + rating_score * 0.3 + engagement_score * 0.2

        return round(momentum, 1)


async def run_daily_capture():
    """Run daily metric capture for all apps."""
    logger.info("Starting daily historical metrics capture...")
    service = HistoricalTrackingService()
    results = await service.capture_daily_metrics()
    logger.info(f"Daily capture complete: {results}")


if __name__ == "__main__":
    import asyncio
    import sys

    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) > 1 and sys.argv[1] == "--capture":
        asyncio.run(run_daily_capture())
