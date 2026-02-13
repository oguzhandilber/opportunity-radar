from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, extract
from app.models.app import App
from app.models.trend import AppTrendHistory
from app.core.database import get_db
import numpy as np
from collections import defaultdict


class SeasonalAnalysisService:
    SEASONAL_EVENTS = {
        "january": ["New Year", "Back to Work", "New Year Fitness"],
        "february": ["Valentine's Day", "Super Bowl", "Presidents Day"],
        "march": ["Spring Break", "St. Patrick's Day", "Tax Season"],
        "april": ["Easter", "Spring", "Earth Day"],
        "may": ["Mother's Day", "Graduation", "Memorial Day"],
        "june": ["Father's Day", "Summer Start", "Pride Month"],
        "july": ["Independence Day", "Vacation Season", "Summer"],
        "august": ["Back to School", "Summer End"],
        "september": ["Back to School", "Fall Start", "Labor Day"],
        "october": ["Halloween", "Q4 Planning", "Spooky Season"],
        "november": ["Thanksgiving", "Black Friday", "Pre-Holiday"],
        "december": ["Christmas", "Holiday Season", "New Year's Eve", "New Year"],
    }

    MONTH_ORDER = {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12,
    }

    def __init__(self):
        self.reverse_month_order = {v: k for k, v in self.MONTH_ORDER.items()}

    async def detect_seasonal_patterns(self, app_id: int) -> Dict[str, Any]:
        """Analyze historical data for seasonal patterns."""
        async for db in get_db():
            # Get historical trend data for the app
            query = (
                db.query(
                    AppTrendHistory,
                    extract("month", AppTrendHistory.created_at).label("month"),
                    extract("year", AppTrendHistory.created_at).label("year"),
                )
                .filter(AppTrendHistory.app_id == app_id)
                .order_by(AppTrendHistory.created_at.desc())
                .limit(365)  # Last year of data
            )

            results = await db.execute(query)
            data = results.all()

            if not data:
                return {
                    "peak_months": [],
                    "low_months": [],
                    "seasonal_score": 0.0,
                    "events_correlated": [],
                    "pattern_strength": "insufficient_data",
                    "recommendations": [
                        "Need more historical data for seasonal analysis"
                    ],
                }

            # Group by month and calculate averages
            monthly_data = defaultdict(list)
            for record, month, year in data:
                monthly_data[int(month)].append(
                    {
                        "revenue": float(record.revenue) if record.revenue else 0,
                        "downloads": record.downloads or 0,
                        "rank": record.rank or 0,
                    }
                )

            # Calculate monthly averages
            monthly_averages = {}
            for month, values in monthly_data.items():
                if len(values) > 1:
                    monthly_averages[month] = {
                        "avg_revenue": np.mean([v["revenue"] for v in values]),
                        "avg_downloads": np.mean([v["downloads"] for v in values]),
                        "avg_rank": np.mean([v["rank"] for v in values]),
                        "data_points": len(values),
                    }

            if not monthly_averages:
                return {
                    "peak_months": [],
                    "low_months": [],
                    "seasonal_score": 0.0,
                    "events_correlated": [],
                    "pattern_strength": "insufficient_data",
                    "recommendations": [
                        "Need more historical data for seasonal analysis"
                    ],
                }

            # Identify peaks and valleys
            revenues = [data["avg_revenue"] for data in monthly_averages.values()]
            revenue_std = np.std(revenues)
            revenue_mean = np.mean(revenues)

            peak_threshold = revenue_mean + revenue_std * 0.5
            low_threshold = revenue_mean - revenue_std * 0.5

            peak_months = []
            low_months = []
            for month, data in monthly_averages.items():
                if data["avg_revenue"] > peak_threshold:
                    peak_months.append(month)
                elif data["avg_revenue"] < low_threshold:
                    low_months.append(month)

            # Calculate seasonal score based on variance
            seasonal_score = (
                min(100.0, (revenue_std / revenue_mean) * 50) if revenue_mean > 0 else 0
            )

            # Detect event correlations
            events_correlated = []
            for month in peak_months:
                month_name = self.reverse_month_order.get(month, "")
                if month_name:
                    events_correlated.extend(
                        self.SEASONAL_EVENTS.get(month_name.lower(), [])
                    )

            # Determine pattern strength
            if seasonal_score > 60:
                pattern_strength = "strong"
            elif seasonal_score > 30:
                pattern_strength = "moderate"
            else:
                pattern_strength = "weak"

            # Generate recommendations
            recommendations = []
            if peak_months:
                peak_month_names = [
                    self.reverse_month_order.get(m, "") for m in peak_months
                ]
                recommendations.append(
                    f"Peak performance in {', '.join(peak_month_names)} - maximize marketing during these periods"
                )

            if 12 in peak_months:  # December
                recommendations.append(
                    "Prepare for Q4 holiday surge - increase inventory and marketing"
                )
            if 6 in peak_months or 7 in peak_months:  # June/July
                recommendations.append("Summer peak - launch seasonal features in May")
            if 8 in peak_months or 9 in peak_months:  # August/September
                recommendations.append(
                    "Back-to-school opportunity - target educational users"
                )

            if not peak_months:
                recommendations.append(
                    "No clear seasonal peaks detected - consider year-round marketing strategy"
                )

            return {
                "peak_months": sorted(peak_months),
                "low_months": sorted(low_months),
                "seasonal_score": round(seasonal_score, 1),
                "events_correlated": list(set(events_correlated)),
                "pattern_strength": pattern_strength,
                "recommendations": recommendations,
            }

    async def predict_seasonal_spike(self, app_id: int, event: str) -> Dict[str, Any]:
        """Predict impact of upcoming event."""
        # Get seasonal patterns first
        patterns = await self.detect_seasonal_patterns(app_id)

        # Find which month this event typically occurs in
        target_month = None
        for month, events in self.SEASONAL_EVENTS.items():
            if event in events:
                target_month = self.MONTH_ORDER.get(month.lower())
                break

        if not target_month:
            return {
                "event": event,
                "predicted_impact": "low",
                "confidence": 0.0,
                "revenue_increase_percent": 0.0,
                "download_increase_percent": 0.0,
                "recommendation": "Event not recognized in seasonal calendar",
            }

        # Check if this is typically a peak month
        is_peak_month = target_month in patterns.get("peak_months", [])
        seasonal_score = patterns.get("seasonal_score", 0)

        # Calculate predicted impact based on historical patterns
        base_impact = "medium" if is_peak_month else "low"
        confidence = (
            0.3 if seasonal_score < 30 else (0.6 if seasonal_score < 60 else 0.8)
        )

        # Estimate percentage increases
        revenue_increase = 15.0 if is_peak_month else 5.0
        download_increase = 20.0 if is_peak_month else 8.0

        # Adjust based on event type
        high_impact_events = [
            "Christmas",
            "Black Friday",
            "New Year",
            "Valentine's Day",
        ]
        medium_impact_events = [
            "Back to School",
            "Halloween",
            "Mother's Day",
            "Father's Day",
        ]

        if event in high_impact_events:
            revenue_increase *= 2.0
            download_increase *= 1.8
            base_impact = "high"
        elif event in medium_impact_events:
            revenue_increase *= 1.5
            download_increase *= 1.3

        # Cap increases at reasonable values
        revenue_increase = min(revenue_increase, 150.0)
        download_increase = min(download_increase, 200.0)

        # Generate specific recommendations
        recommendations = []
        if event in ["Christmas", "Holiday Season", "New Year"]:
            recommendations.extend(
                [
                    "Launch holiday-themed features 2 weeks before peak",
                    "Increase marketing budget by 40% during event period",
                    "Prepare for increased server load",
                ]
            )
        elif event == "Back to School":
            recommendations.extend(
                [
                    "Target parents and students in marketing campaigns",
                    "Offer educational discounts or bundles",
                    "Align app features with academic calendar",
                ]
            )
        elif event in ["Valentine's Day", "Mother's Day", "Father's Day"]:
            recommendations.extend(
                [
                    "Create gift-focused promotions",
                    "Use emotional marketing appeals",
                    "Offer limited-time special editions",
                ]
            )
        else:
            recommendations.extend(
                [
                    f"Monitor performance closely during {event} period",
                    "Consider event-specific promotional content",
                    "Test different marketing messages",
                ]
            )

        return {
            "event": event,
            "target_month": target_month,
            "predicted_impact": base_impact,
            "confidence": round(confidence, 2),
            "revenue_increase_percent": round(revenue_increase, 1),
            "download_increase_percent": round(download_increase, 1),
            "recommendation": recommendations[0]
            if recommendations
            else "Monitor performance during event",
            "actionable_recommendations": recommendations,
        }

    async def calculate_seasonal_score(self, app_id: int, target_month: int) -> float:
        """Calculate seasonal opportunity score (0-100)."""
        patterns = await self.detect_seasonal_patterns(app_id)

        base_score = patterns.get("seasonal_score", 0)

        # Boost score if target month is a peak month
        if target_month in patterns.get("peak_months", []):
            base_score = min(100, base_score + 20)
        # Reduce score if target month is a low month
        elif target_month in patterns.get("low_months", []):
            base_score = max(0, base_score - 15)

        # Additional factors
        month_name = self.reverse_month_order.get(target_month, "").lower()
        events = self.SEASONAL_EVENTS.get(month_name, [])

        # High-value events boost score
        high_value_events = ["Christmas", "Black Friday", "New Year", "Valentine's Day"]
        for event in events:
            if event in high_value_events:
                base_score = min(100, base_score + 15)
                break

        return round(base_score, 1)

    async def get_upcoming_opportunities(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get apps with upcoming seasonal opportunities."""
        current_date = datetime.now()
        end_date = current_date + timedelta(days=days)

        opportunities = []

        async for db in get_db():
            # Get all apps
            apps_query = db.query(App).all()
            apps = await db.execute(apps_query)

            for app in apps.scalars():
                # Calculate seasonal scores for upcoming months
                current_month = current_date.month
                target_months = []

                # Include current month and next 2 months
                for i in range(3):
                    month = ((current_month + i - 1) % 12) + 1
                    target_months.append(month)

                best_score = 0
                best_month = None

                for month in target_months:
                    score = await self.calculate_seasonal_score(app.id, month)
                    if score > best_score:
                        best_score = score
                        best_month = month

                # Only include apps with significant opportunity
                if best_score >= 30:
                    month_name = self.reverse_month_order.get(best_month, "").title()
                    events = self.SEASONAL_EVENTS.get(month_name.lower(), [])

                    opportunities.append(
                        {
                            "app_id": app.id,
                            "app_name": app.name,
                            "category": app.category,
                            "best_month": best_month,
                            "month_name": month_name,
                            "seasonal_score": best_score,
                            "upcoming_events": events,
                            "days_until_month": self._days_until_month(
                                current_date, best_month
                            ),
                            "priority": "high"
                            if best_score >= 70
                            else ("medium" if best_score >= 50 else "low"),
                        }
                    )

        # Sort by score and priority
        opportunities.sort(key=lambda x: (-x["seasonal_score"], x["days_until_month"]))

        return opportunities[:20]  # Return top 20 opportunities

    def _days_until_month(self, current_date: datetime, target_month: int) -> int:
        """Calculate days until target month starts."""
        current_year = current_date.year
        current_month = current_date.month

        if target_month >= current_month:
            target_year = current_year
        else:
            target_year = current_year + 1

        target_date = datetime(target_year, target_month, 1)
        return (target_date - current_date).days

    async def get_monthly_opportunities_report(
        self, months_ahead: int = 3
    ) -> Dict[str, Any]:
        """Generate comprehensive monthly opportunities report."""
        current_date = datetime.now()
        report = {
            "months": [],
            "summary": {"total_opportunities": 0, "high_priority": 0},
        }

        for i in range(months_ahead):
            month_num = ((current_date.month + i - 1) % 12) + 1
            year = current_date.year + (current_date.month + i - 1) // 12
            month_name = self.reverse_month_order.get(month_num, "").title()

            opportunities = []
            async for db in get_db():
                apps_query = db.query(App).all()
                apps = await db.execute(apps_query)

                for app in apps.scalars():
                    score = await self.calculate_seasonal_score(app.id, month_num)
                    if score >= 40:  # Only include meaningful opportunities
                        events = self.SEASONAL_EVENTS.get(month_name.lower(), [])
                        opportunities.append(
                            {
                                "app_id": app.id,
                                "app_name": app.name,
                                "category": app.category,
                                "score": score,
                                "events": events,
                            }
                        )

            opportunities.sort(key=lambda x: x["score"], reverse=True)

            month_data = {
                "month": month_name,
                "month_number": month_num,
                "year": year,
                "events": self.SEASONAL_EVENTS.get(month_name.lower(), []),
                "opportunities": opportunities[:10],  # Top 10 per month
                "opportunity_count": len(opportunities),
            }

            report["months"].append(month_data)
            report["summary"]["total_opportunities"] += len(opportunities)
            report["summary"]["high_priority"] += len(
                [o for o in opportunities if o["score"] >= 70]
            )

        return report
