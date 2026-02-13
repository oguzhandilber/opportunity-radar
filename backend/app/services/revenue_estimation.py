"""Revenue Estimation Service for App Store applications.

Estimates monthly and yearly revenue for apps based on:
- Category benchmarks (ARPU per 1000 downloads)
- Rating count and velocity
- Age factors
- Price points
- Download estimates from ratings
"""

import logging
import math
from typing import Any, Dict

from app.database import get_db_context
from app.models.app_store import (
    AppStoreApp,
    CATEGORY_REVENUE_BENCHMARKS,
)

logger = logging.getLogger(__name__)


class RevenueEstimationService:
    """Service for estimating app revenue from store metrics."""

    def __init__(self):
        # Category revenue benchmarks (monthly revenue per 1000 downloads)
        self.category_benchmarks = CATEGORY_REVENUE_BENCHMARKS.copy()

    async def estimate_revenue(self, app: AppStoreApp) -> Dict[str, Any]:
        """Estimate monthly and yearly revenue for an app."""
        try:
            category_name = app.category.name if app.category else "Unknown"

            download_estimate = await self.estimate_downloads(app)

            monthly_revenue = await self.calculate_revenue(
                download_estimate,
                category_name,
                app.rating or 0.0,
                app.price or 0.0,
            )

            confidence = await self.calculate_confidence(app)

            breakdown = await self.get_revenue_breakdown(app)
            breakdown["download_estimate"] = download_estimate

            yearly_revenue = monthly_revenue * 12

            confidence_range = 1.0 - confidence  # Lower confidence = wider range
            low_estimate = monthly_revenue * (1.0 - confidence_range)
            high_estimate = monthly_revenue * (1.0 + confidence_range)

            return {
                "monthly_revenue_estimate": round(monthly_revenue, 2),
                "yearly_revenue_estimate": round(yearly_revenue, 2),
                "confidence_score": round(confidence, 3),
                "download_estimate": download_estimate,
                "breakdown": breakdown,
                "revenue_range": {
                    "low": round(low_estimate, 2),
                    "high": round(high_estimate, 2),
                },
            }
        except Exception as e:
            logger.error(f"Error estimating revenue for app {app.id}: {e}")
            return {
                "monthly_revenue_estimate": 0.0,
                "yearly_revenue_estimate": 0.0,
                "confidence_score": 0.0,
                "download_estimate": 0,
                "breakdown": {},
                "revenue_range": {"low": 0.0, "high": 0.0},
            }

    async def estimate_downloads(self, app: AppStoreApp) -> int:
        """Estimate total downloads from ratings."""
        # Base: 100-200 downloads per rating (average 150)
        base_downloads_per_rating = 150

        # Age factor: newer apps may have fewer total ratings
        if app.age_in_days:
            age_factor = min(1.0, 365 / max(app.age_in_days, 1))
        else:
            age_factor = 1.0

        # Rating velocity factor (recent growth = more downloads)
        if app.current_rating_count and app.rating_count:
            velocity = app.current_rating_count / max(app.rating_count, 1)
            velocity_factor = 1 + (velocity * 0.5)
        else:
            velocity_factor = 1.0

        return int(
            app.rating_count * base_downloads_per_rating * age_factor * velocity_factor
        )

    async def calculate_revenue(
        self, downloads: int, category: str, rating: float, price: float
    ) -> float:
        """Calculate monthly revenue."""
        # Category benchmark (ARPU = revenue per 1000 downloads)
        arpu = self.category_benchmarks.get(category, 20.0)

        # Category multiplier (up to 2x for high-value categories)
        category_multiplier = arpu / 20.0

        # Rating multiplier (higher rating = more willingness to pay)
        rating_multiplier = 1.0 + ((rating - 3.0) * 0.2)
        rating_multiplier = max(0.1, rating_multiplier)  # Clamp minimum

        # Price factor (paid apps have higher ARPU)
        if price > 0:
            price_factor = 1 + (price / 10.0)  # Each $10 adds 10% to ARPU
        else:
            price_factor = 0.5  # Free apps have lower ARPU

        return (downloads / 1000) * arpu * rating_multiplier * price_factor

    async def calculate_confidence(self, app: AppStoreApp) -> float:
        """Calculate confidence score (0.0-1.0) for the estimate."""
        confidence = 0.5  # Base confidence

        # More ratings = higher confidence
        if app.rating_count:
            if app.rating_count > 100000:
                confidence += 0.3
            elif app.rating_count > 10000:
                confidence += 0.2
            elif app.rating_count > 1000:
                confidence += 0.1
            elif app.rating_count > 100:
                confidence += 0.05

        # Recent ratings indicate fresh data
        if app.current_rating_count and app.rating_count:
            velocity = app.current_rating_count / max(app.rating_count, 1)
            if velocity > 0.1:  # >10% recent ratings
                confidence += 0.1

        # Higher ratings indicate stable apps
        if app.rating and app.rating >= 4.0:
            confidence += 0.05
        elif app.rating and app.rating < 3.0:
            confidence -= 0.1

        # Price point indicates monetization strategy clarity
        if app.price and app.price > 0:
            confidence += 0.05

        # Age factor (established apps are easier to predict)
        if app.age_in_days:
            if app.age_in_days > 365:  # >1 year
                confidence += 0.05
            elif app.age_in_days < 30:  # <1 month
                confidence -= 0.1

        return max(0.0, min(1.0, confidence))

    async def get_revenue_breakdown(self, app: AppStoreApp) -> Dict[str, Any]:
        """Get detailed breakdown of revenue factors."""
        category_name = app.category.name if app.category else "Unknown"

        category_benchmark = self.category_benchmarks.get(category_name, 20.0)

        rating = app.rating or 0.0
        rating_factor = 1.0 + ((rating - 3.0) * 0.2)
        rating_factor = max(0.1, rating_factor)

        price = app.price or 0.0
        if price > 0:
            price_factor = 1 + (price / 10.0)
        else:
            price_factor = 0.5

        if app.current_rating_count and app.rating_count:
            velocity = app.current_rating_count / max(app.rating_count, 1)
            velocity_factor = 1 + (velocity * 0.5)
        else:
            velocity_factor = 1.0

        if app.age_in_days:
            age_factor = min(1.0, 365 / max(app.age_in_days, 1))
        else:
            age_factor = 1.0

        return {
            "category_benchmark": category_benchmark,
            "rating_factor": round(rating_factor, 3),
            "price_factor": round(price_factor, 3),
            "velocity_factor": round(velocity_factor, 3),
            "age_factor": round(age_factor, 3),
        }

    async def update_app_revenue_estimates(self, app_id: int) -> bool:
        """Update revenue estimates for an app in the database."""
        try:
            async with get_db_context() as session:
                from sqlalchemy import select
                from sqlalchemy.orm import selectinload

                query = (
                    select(AppStoreApp)
                    .options(selectinload(AppStoreApp.category))
                    .where(AppStoreApp.id == app_id)
                )
                result = await session.execute(query)
                app = result.scalar_one_or_none()

                if not app:
                    logger.warning(f"App {app_id} not found for revenue estimation")
                    return False

                estimates = await self.estimate_revenue(app)

                app.monthly_revenue_estimate = int(
                    estimates["monthly_revenue_estimate"]
                )
                app.yearly_revenue_estimate = int(estimates["yearly_revenue_estimate"])
                app.revenue_confidence = estimates["confidence_score"]
                app.download_estimate = estimates["download_estimate"]

                await session.commit()
                logger.info(f"Updated revenue estimates for app {app_id}")
                return True

        except Exception as e:
            logger.error(f"Error updating revenue estimates for app {app_id}: {e}")
            return False

    async def estimate_revenue_for_all_apps(
        self, batch_size: int = 50
    ) -> Dict[str, int]:
        """Estimate revenue for all apps in the database."""
        try:
            async with get_db_context() as session:
                from sqlalchemy import select

                query = select(AppStoreApp.id)
                result = await session.execute(query)
                app_ids = [row[0] for row in result.fetchall()]

            updated = 0
            errors = 0

            for app_id in app_ids:
                try:
                    success = await self.update_app_revenue_estimates(app_id)
                    if success:
                        updated += 1
                    else:
                        errors += 1
                except Exception as e:
                    logger.error(f"Error estimating revenue for app {app_id}: {e}")
                    errors += 1

            return {"updated": updated, "errors": errors}

        except Exception as e:
            logger.error(f"Error in bulk revenue estimation: {e}")
            return {
                "updated": 0,
                "errors": len(app_ids) if "app_ids" in locals() else 0,
            }


async def run_revenue_estimation_service():
    """Run the revenue estimation service for all apps."""
    logger.info("Starting revenue estimation service...")
    service = RevenueEstimationService()
    results = await service.estimate_revenue_for_all_apps()
    logger.info(f"Revenue estimation complete: {results}")


if __name__ == "__main__":
    import asyncio
    import logging

    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_revenue_estimation_service())
