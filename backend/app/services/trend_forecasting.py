import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
import statistics

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.analyzers.ai_client import get_ai_client
from app.database import get_db_context
from app.models.app_store import (
    AppStoreApp,
    AppForecast,
    AppTrendHistory,
    AppViralHistory,
    AppRevenueHistory,
    AppStoreCategory,
)

logger = logging.getLogger(__name__)


class TrendForecastingService:
    def __init__(self):
        self.ai_client = get_ai_client()

    async def forecast_trends(
        self, days: int = 7, category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        async with get_db_context() as session:
            apps = await self._get_apps_to_forecast(session, category)
            forecasts = []

            for app in apps:
                try:
                    forecast = await self.forecast_app_trend(app.id, days)
                    if forecast:
                        forecasts.append(forecast)
                except Exception as e:
                    logger.error(f"Error forecasting app {app.id}: {e}")
                    continue

            forecasts.sort(key=lambda x: x["predicted_score"], reverse=True)
            return forecasts

    async def forecast_app_trend(self, app_id: int, days: int = 7) -> Dict[str, Any]:
        async with get_db_context() as session:
            app = await self._get_app_with_history(session, app_id)
            if not app:
                return {}

            velocity_factor = await self._calculate_velocity_factor(app, days)
            seasonal_factor = await self._calculate_seasonal_factor(app, days)
            viral_factor = await self._calculate_viral_factor(app, days)
            category_factor = await self._calculate_category_factor(app, days)

            weights = {
                "velocity": 0.4,
                "seasonal": 0.25,
                "viral": 0.2,
                "category": 0.15,
            }
            forecast_score = (
                velocity_factor * weights["velocity"]
                + seasonal_factor * weights["seasonal"]
                + viral_factor * weights["viral"]
                + category_factor * weights["category"]
            ) * 100

            current_score = float(
                getattr(app.scores, "total_opportunity_score", 0) if app.scores else 0
            ) or float(app.engagement_score or 50)
            trend_direction = self._determine_trend_direction(
                current_score, forecast_score
            )

            confidence = await self.calculate_confidence(app_id, days)

            reasoning = await self._generate_forecast_reasoning(
                app,
                velocity_factor,
                seasonal_factor,
                viral_factor,
                category_factor,
                days,
            )

            recommendations = await self._generate_recommendations(app, trend_direction)
            risk_level = self._determine_risk_level(confidence, trend_direction)

            forecast = {
                "forecast_id": f"app_{app_id}_{days}d",
                "app_id": app_id,
                "app_name": app.name,
                "forecast_days": days,
                "predicted_trend": trend_direction,
                "current_score": current_score,
                "predicted_score": round(forecast_score, 1),
                "confidence": confidence,
                "reasoning": reasoning,
                "factors": {
                    "velocity_factor": round(velocity_factor, 3),
                    "seasonal_factor": round(seasonal_factor, 3),
                    "viral_factor": round(viral_factor, 3),
                    "category_factor": round(category_factor, 3),
                },
                "risk_level": risk_level,
                "recommendations": recommendations,
                "created_at": datetime.now(timezone.utc),
            }

            await self._save_forecast(session, forecast)
            return forecast

    async def calculate_confidence(self, app_id: int, days: int) -> float:
        async with get_db_context() as session:
            app = await self._get_app_with_history(session, app_id)
            if not app:
                return 0.5

            confidence_factors = []

            if len(app.trend_history) >= 30:
                confidence_factors.append(0.9)
            elif len(app.trend_history) >= 14:
                confidence_factors.append(0.7)
            elif len(app.trend_history) >= 7:
                confidence_factors.append(0.5)
            else:
                confidence_factors.append(0.3)

            rating_count = int(app.rating_count or 0)
            if rating_count > 100000:
                confidence_factors.append(0.9)
            elif rating_count > 10000:
                confidence_factors.append(0.7)
            elif rating_count > 1000:
                confidence_factors.append(0.5)
            else:
                confidence_factors.append(0.4)

            age_in_days = int(app.age_in_days or 0)
            if 30 <= age_in_days <= 365:
                confidence_factors.append(0.8)
            elif age_in_days < 30:
                confidence_factors.append(0.4)
            elif age_in_days > 1825:
                confidence_factors.append(0.6)
            else:
                confidence_factors.append(0.7)

            if app.current_rating_count and app.rating_count:
                velocity_ratio = int(app.current_rating_count) / max(
                    1, int(app.rating_count)
                )
                if velocity_ratio > 0.1:
                    confidence_factors.append(0.8)
                elif velocity_ratio > 0.05:
                    confidence_factors.append(0.6)
                else:
                    confidence_factors.append(0.4)

            return round(statistics.mean(confidence_factors), 2)

    async def explain_forecast(self, app_id: int, days: int) -> Dict[str, Any]:
        async with get_db_context() as session:
            app = await self._get_app_with_history(session, app_id)
            if not app:
                return {}

            forecast = await self._get_latest_forecast(session, app_id, days)
            if not forecast:
                return {}

            velocity_analysis = await self._analyze_velocity_patterns(app, days)
            seasonal_analysis = await self._analyze_seasonal_patterns(app, days)
            viral_analysis = await self._analyze_viral_patterns(app, days)
            category_analysis = await self._analyze_category_patterns(app, days)

            ai_explanation = await self._generate_ai_explanation(app, forecast)

            return {
                "app_id": app_id,
                "app_name": app.name,
                "forecast_summary": {
                    "trend": forecast.predicted_trend,
                    "confidence": forecast.confidence,
                    "predicted_score": forecast.confidence * 100,
                },
                "velocity_analysis": velocity_analysis,
                "seasonal_analysis": seasonal_analysis,
                "viral_analysis": viral_analysis,
                "category_analysis": category_analysis,
                "ai_explanation": ai_explanation,
                "detailed_factors": forecast.factors or {},
                "created_at": forecast.created_at,
            }

    async def _get_apps_to_forecast(
        self, session: AsyncSession, category: Optional[str]
    ) -> List[AppStoreApp]:
        query = select(AppStoreApp).options(
            selectinload(AppStoreApp.category),
            selectinload(AppStoreApp.trend_history),
            selectinload(AppStoreApp.scores),
        )

        if category:
            query = query.join(AppStoreCategory).where(
                AppStoreCategory.name == category
            )

        query = query.where(
            or_(
                AppStoreApp.rating_count > 100,
                AppStoreApp.is_rising == True,
                AppStoreApp.is_new_release == True,
            )
        ).limit(100)

        result = await session.execute(query)
        return list(result.scalars().all())

    async def _get_app_with_history(
        self, session: AsyncSession, app_id: int
    ) -> Optional[AppStoreApp]:
        query = (
            select(AppStoreApp)
            .options(
                selectinload(AppStoreApp.category),
                selectinload(AppStoreApp.trend_history),
                selectinload(AppStoreApp.viral_history),
                selectinload(AppStoreApp.revenue_history),
                selectinload(AppStoreApp.scores),
            )
            .where(AppStoreApp.id == app_id)
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def _calculate_velocity_factor(self, app: AppStoreApp, days: int) -> float:
        if not app.trend_history or len(app.trend_history) < 3:
            return 0.5

        recent_history = sorted(
            app.trend_history, key=lambda x: x.recorded_at, reverse=True
        )[: min(7, len(app.trend_history))]

        rating_velocities = []
        for record in recent_history:
            if record.rating_velocity:
                rating_velocities.append(record.rating_velocity)

        if not rating_velocities:
            rating_velocities.append(0)

        avg_velocity = statistics.mean(rating_velocities)
        normalized_velocity = min(1.0, max(0.0, avg_velocity / 100))

        trend_direction = str(app.trend_direction or "stable")
        if trend_direction == "up":
            normalized_velocity = min(1.0, normalized_velocity * 1.2)
        elif trend_direction == "down":
            normalized_velocity = max(0.0, normalized_velocity * 0.8)

        return normalized_velocity

    async def _calculate_seasonal_factor(self, app: AppStoreApp, days: int) -> float:
        if not app.category:
            return 0.5

        seasonal_data = getattr(app, "seasonal_pattern", {})
        if not seasonal_data:
            return 0.5

        current_month = datetime.now().month
        peak_months = seasonal_data.get("peak_months", [])

        if current_month in peak_months:
            return 0.9
        elif any(abs(current_month - pm) <= 2 for pm in peak_months):
            return 0.7
        else:
            return 0.5

    async def _calculate_viral_factor(self, app: AppStoreApp, days: int) -> float:
        viral_score = float(getattr(app, "viral_score", 0.0))
        viral_velocity = float(getattr(app, "viral_velocity", 0.0))

        if viral_score > 0:
            return min(1.0, viral_score / 100)
        elif viral_velocity > 0:
            return min(1.0, viral_velocity / 50)
        elif bool(app.early_viral_signal):
            return 0.7
        else:
            return 0.3

    async def _calculate_category_factor(self, app: AppStoreApp, days: int) -> float:
        if not app.category:
            return 0.5

        category = app.category
        growth_indicators = []

        if category.app_count > 1000:
            growth_indicators.append(0.8)
        elif category.app_count > 100:
            growth_indicators.append(0.6)
        else:
            growth_indicators.append(0.4)

        if category.average_rating >= 4.0:
            growth_indicators.append(0.8)
        elif category.average_rating >= 3.5:
            growth_indicators.append(0.6)
        else:
            growth_indicators.append(0.4)

        if category.revenue_benchmark > 50:
            growth_indicators.append(0.8)
        elif category.revenue_benchmark > 20:
            growth_indicators.append(0.6)
        else:
            growth_indicators.append(0.4)

        return statistics.mean(growth_indicators)

    def _determine_trend_direction(
        self, current_score: float, forecast_score: float
    ) -> str:
        diff = forecast_score - current_score
        if diff > 10:
            return "rising"
        elif diff < -10:
            return "falling"
        else:
            return "stable"

    async def _generate_forecast_reasoning(
        self,
        app: AppStoreApp,
        velocity_factor: float,
        seasonal_factor: float,
        viral_factor: float,
        category_factor: float,
        days: int,
    ) -> List[str]:
        reasoning = []

        if velocity_factor > 0.7:
            reasoning.append("High velocity growth detected")
        elif velocity_factor > 0.5:
            reasoning.append("Moderate velocity growth")
        elif velocity_factor < 0.3:
            reasoning.append("Low velocity indicators")

        if seasonal_factor > 0.8:
            reasoning.append("Strong seasonal alignment")
        elif seasonal_factor > 0.6:
            reasoning.append("Moderate seasonal factors")

        if viral_factor > 0.7:
            reasoning.append("Positive viral signals detected")
        elif viral_factor > 0.5:
            reasoning.append("Emerging viral indicators")

        if category_factor > 0.7:
            reasoning.append("Strong category momentum")
        elif category_factor > 0.5:
            reasoning.append("Moderate category growth")

        if bool(app.is_new_release):
            reasoning.append("New release boost potential")
        if bool(app.is_rising):
            reasoning.append("Already showing rising momentum")
        if app.rating and app.rating >= 4.5:
            reasoning.append("High user satisfaction drives growth")

        return reasoning

    async def _generate_recommendations(
        self, app: AppStoreApp, trend_direction: str
    ) -> List[str]:
        recommendations = []

        if trend_direction == "rising":
            recommendations.extend(
                [
                    "Monitor daily for momentum confirmation",
                    "Prepare marketing campaigns for peak interest",
                    "Consider feature acceleration to capitalize on growth",
                ]
            )
        elif trend_direction == "falling":
            recommendations.extend(
                [
                    "Investigate cause of decline immediately",
                    "Consider price adjustments or feature updates",
                    "Monitor competitor movements closely",
                ]
            )
        else:
            recommendations.extend(
                [
                    "Maintain current strategy while monitoring changes",
                    "Focus on user retention and engagement",
                    "Explore incremental feature improvements",
                ]
            )

        if app.category and app.category.name in ["Finance", "Business"]:
            recommendations.append("Focus on enterprise features and security")

        return recommendations

    def _determine_risk_level(self, confidence: float, trend_direction: str) -> str:
        if confidence > 0.8:
            return "low"
        elif confidence > 0.6:
            return "high" if trend_direction == "falling" else "medium"
        else:
            return "high"

    async def _save_forecast(
        self, session: AsyncSession, forecast_data: Dict[str, Any]
    ) -> AppForecast:
        forecast = AppForecast(
            app_id=forecast_data["app_id"],
            forecast_days=forecast_data["forecast_days"],
            predicted_trend=forecast_data["predicted_trend"],
            confidence=forecast_data["confidence"],
            reasoning="; ".join(forecast_data["reasoning"]),
            factors=forecast_data["factors"],
        )
        session.add(forecast)
        await session.commit()
        await session.refresh(forecast)
        return forecast

    async def _get_latest_forecast(
        self, session: AsyncSession, app_id: int, days: int
    ) -> Optional[AppForecast]:
        query = (
            select(AppForecast)
            .where(AppForecast.app_id == app_id, AppForecast.forecast_days == days)
            .order_by(AppForecast.created_at.desc())
            .limit(1)
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def _analyze_velocity_patterns(
        self, app: AppStoreApp, days: int
    ) -> Dict[str, Any]:
        if not app.trend_history:
            return {"analysis": "Insufficient velocity data"}

        recent_history = sorted(
            app.trend_history, key=lambda x: x.recorded_at, reverse=True
        )[:14]

        velocities = [float(h.rating_velocity or 0) for h in recent_history]
        if not velocities:
            return {"analysis": "No velocity measurements available"}

        trend = "increasing" if velocities[-1] > velocities[0] else "decreasing"
        avg_velocity = statistics.mean(velocities)

        return {
            "trend": trend,
            "average_velocity": round(avg_velocity, 2),
            "latest_velocity": round(velocities[-1], 2),
            "velocity_stability": 1
            - (statistics.stdev(velocities) / max(avg_velocity, 1)),
        }

    async def _analyze_seasonal_patterns(
        self, app: AppStoreApp, days: int
    ) -> Dict[str, Any]:
        seasonal_data = getattr(app, "seasonal_pattern", {})
        if not seasonal_data:
            return {"analysis": "No seasonal data available"}

        current_month = datetime.now().month
        peak_months = seasonal_data.get("peak_months", [])
        score = float(seasonal_data.get("score", 0.0))

        return {
            "current_month": current_month,
            "peak_months": peak_months,
            "is_peak_season": current_month in peak_months,
            "seasonal_score": score,
            "events": seasonal_data.get("events", []),
        }

    async def _analyze_viral_patterns(
        self, app: AppStoreApp, days: int
    ) -> Dict[str, Any]:
        viral_score = float(getattr(app, "viral_score", 0.0))
        viral_velocity = float(getattr(app, "viral_velocity", 0.0))
        coefficient = float(getattr(app, "viral_coefficient", 0.0))

        if viral_history := app.viral_history:
            recent_viral = sorted(
                viral_history, key=lambda x: x.recorded_at, reverse=True
            )[:7]
            recent_scores = [float(v.viral_score or 0) for v in recent_viral]
            viral_trend = (
                "increasing" if recent_scores[-1] > recent_scores[0] else "decreasing"
            )
        else:
            viral_trend = "stable"

        return {
            "current_score": viral_score,
            "velocity": viral_velocity,
            "coefficient": coefficient,
            "trend": viral_trend,
            "early_signals": bool(app.early_viral_signal),
        }

    async def _analyze_category_patterns(
        self, app: AppStoreApp, days: int
    ) -> Dict[str, Any]:
        if not app.category:
            return {"analysis": "No category data"}

        return {
            "category": app.category.name,
            "app_count": app.category.app_count,
            "average_rating": app.category.average_rating,
            "revenue_benchmark": app.category.revenue_benchmark,
            "complexity_multiplier": app.category.complexity_multiplier,
        }

    async def _generate_ai_explanation(
        self, app: AppStoreApp, forecast: AppForecast
    ) -> str:
        prompt = f"""
        Explain this app trend forecast in 2-3 sentences:
        
        App: {app.name}
        Category: {app.category.name if app.category else "Unknown"}
        Current Rating: {app.rating} ({app.rating_count} reviews)
        
        Forecast: {forecast.predicted_trend} trend
        Confidence: {forecast.confidence:.0%}
        Key Factors: {forecast.factors}
        
        Focus on why this trend is expected and what it means for opportunity.
        """

        try:
            result = await self.ai_client.complete(prompt)
            return result.strip()
        except Exception as e:
            logger.error(f"AI explanation error: {e}")
            return (
                f"Expected {forecast.predicted_trend} trend based on market indicators."
            )


async def run_forecast_service():
    logger.info("Starting trend forecasting service...")
    service = TrendForecastingService()

    forecasts_7d = await service.forecast_trends(days=7)
    logger.info(f"Generated {len(forecasts_7d)} 7-day forecasts")

    forecasts_30d = await service.forecast_trends(days=30)
    logger.info(f"Generated {len(forecasts_30d)} 30-day forecasts")

    return {"forecasts_7d": len(forecasts_7d), "forecasts_30d": len(forecasts_30d)}


if __name__ == "__main__":
    import asyncio
    import sys

    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) > 1 and sys.argv[1] == "--forecast":
        asyncio.run(run_forecast_service())
