"""Viral Detection Service for App Store apps.

Analyzes apps for viral potential and detects early viral signals.
Calculates viral scores, K-factor, and provides comprehensive viral metrics.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_context
from app.models.app_store import (
    AppStoreApp,
    AppViralHistory,
)

logger = logging.getLogger(__name__)


class ViralDetectionService:
    """Service for detecting viral potential and early viral signals in apps."""

    async def calculate_viral_score(self, app_id: int) -> float:
        """Calculate viral potential score (0-100).

        Factors:
        - Rating velocity (30%)
        - Download velocity (25%)
        - Engagement rate (20%)
        - Shareability score (15%)
        - Timing/seasonality (10%)
        """
        velocity_score = await self._calculate_velocity_score(app_id)
        engagement_score = await self._calculate_engagement_score(app_id)
        shareability_score = await self._calculate_shareability_score(app_id)
        timing_score = await self._calculate_timing_score(app_id)
        k_factor = await self.calculate_k_factor(app_id)

        viral_score = (
            velocity_score * 0.30
            + engagement_score * 0.25
            + shareability_score * 0.20
            + timing_score * 0.10
            + k_factor * 0.15
        )

        return round(viral_score, 1)

    async def detect_early_viral(self, app_id: int) -> Dict[str, Any]:
        """Detect early viral signals."""
        signals = []
        confidence = 0.0

        async with get_db_context() as session:
            app = await self._get_app(session, app_id)
            if not app:
                return self._empty_viral_signal()

            # Check for rating spike
            rating_spike = self._detect_rating_spike(app)
            if rating_spike["detected"]:
                signals.append("rating_spike")
                confidence += rating_spike["confidence"]

            # Check for download acceleration
            download_accel = self._detect_download_acceleration(app)
            if download_accel["detected"]:
                signals.append("download_acceleration")
                confidence += download_accel["confidence"]

            # Check for social buzz indicators
            social_buzz = self._detect_social_buzz(app)
            if social_buzz["detected"]:
                signals.append("social_buzz")
                confidence += social_buzz["confidence"]

            # Check for media mentions
            media_mention = self._detect_media_mentions(app)
            if media_mention["detected"]:
                signals.append("media_mention")
                confidence += media_mention["confidence"]

            # Check for category breakthrough
            category_breakthrough = self._detect_category_breakthrough(app)
            if category_breakthrough["detected"]:
                signals.append("category_breakthrough")
                confidence += category_breakthrough["confidence"]

            confidence = min(1.0, confidence)
            is_early_viral = confidence > 0.6 and len(signals) >= 2

            hours_to_viral = self._estimate_hours_to_viral(confidence, len(signals))
            recommended_actions = self._get_recommended_actions(confidence, signals)

            return {
                "is_early_viral": is_early_viral,
                "signals_detected": signals,
                "confidence": round(confidence, 2),
                "hours_to_viral": hours_to_viral,
                "recommended_actions": recommended_actions,
                "viral_score": await self.calculate_viral_score(app_id),
                "k_factor": await self.calculate_k_factor(app_id),
            }

    async def calculate_k_factor(self, app_id: int) -> float:
        """Calculate viral coefficient (K-factor).

        K = i × c
        Where:
        - i = number of invitations sent by each customer
        - c = conversion rate of invitations

        K > 1 = viral growth
        K < 1 = non-viral
        """
        async with get_db_context() as session:
            app = await self._get_app(session, app_id)
            if not app:
                return 0.0

            # Estimate invitations per user (i)
            invitations = self._estimate_invitations_per_user(app)

            # Estimate conversion rate (c)
            conversion_rate = self._estimate_conversion_rate(app)

            # Calculate K-factor
            k_factor = invitations * conversion_rate

            # Normalize to 0-100 scale for scoring
            # K=1 maps to score=50, K=2 maps to score=100
            if k_factor <= 0:
                normalized_score = 0.0
            elif k_factor >= 2.0:
                normalized_score = 100.0
            else:
                normalized_score = (k_factor / 2.0) * 100

            return round(normalized_score, 1)

    async def get_viral_metrics(self, app_id: int) -> Dict[str, Any]:
        """Get comprehensive viral metrics for an app."""
        async with get_db_context() as session:
            app = await self._get_app(session, app_id)
            if not app:
                return {}

            viral_score = await self.calculate_viral_score(app_id)
            k_factor = await self.calculate_k_factor(app_id)
            early_viral = await self.detect_early_viral(app_id)

            # Get historical viral data
            history = await self._get_viral_history(session, app_id, days=30)

            return {
                "app_id": app_id,
                "app_name": app.name,
                "viral_score": viral_score,
                "k_factor": k_factor,
                "early_viral_detection": early_viral,
                "velocity_metrics": {
                    "rating_velocity": self._calculate_rating_velocity(app),
                    "download_velocity": self._calculate_download_velocity(app),
                    "engagement_velocity": self._calculate_engagement_velocity(app),
                },
                "shareability_metrics": {
                    "social_sharing_potential": self._calculate_social_sharing_potential(
                        app
                    ),
                    "viral_coefficient_raw": k_factor
                    / 100.0
                    * 2.0,  # Convert back to K-factor
                    "network_effects_score": self._calculate_network_effects_score(app),
                },
                "historical_trends": {
                    "viral_score_trend": self._calculate_viral_score_trend(history),
                    "peak_viral_score": max([h["viral_score"] for h in history] + [0]),
                    "viral_growth_rate": self._calculate_viral_growth_rate(history),
                },
                "signals": {
                    "current_signals": early_viral["signals_detected"],
                    "signal_strength": early_viral["confidence"],
                    "time_to_viral": early_viral["hours_to_viral"],
                },
                "recommendations": early_viral["recommended_actions"],
                "last_analyzed": datetime.now(timezone.utc).isoformat(),
            }

    async def detect_viral_alerts(self) -> List[Dict[str, Any]]:
        """Detect apps currently going viral."""
        viral_apps = []

        async with get_db_context() as session:
            # Get apps with high viral potential
            query = (
                select(AppStoreApp)
                .where(
                    AppStoreApp.viral_score > 70.0,
                    AppStoreApp.early_viral_signal == True,
                )
                .limit(50)
            )

            result = await session.execute(query)
            apps = result.scalars().all()

            for app in apps:
                early_viral = await self.detect_early_viral(app.id)

                if early_viral["is_early_viral"] and early_viral["confidence"] > 0.7:
                    viral_apps.append(
                        {
                            "app_id": app.id,
                            "app_name": app.name,
                            "developer": app.developer,
                            "category": app.category.name if app.category else None,
                            "viral_score": app.viral_score,
                            "confidence": early_viral["confidence"],
                            "signals": early_viral["signals_detected"],
                            "hours_to_viral": early_viral["hours_to_viral"],
                            "urgency": self._calculate_urgency(early_viral),
                            "recommendations": early_viral["recommended_actions"],
                            "trend_direction": app.trend_direction,
                            "rating_velocity": self._calculate_rating_velocity(app),
                        }
                    )

        # Sort by confidence and urgency
        viral_apps.sort(key=lambda x: (x["confidence"], x["urgency"]), reverse=True)

        return viral_apps[:10]  # Return top 10 most viral apps

    async def _calculate_velocity_score(self, app_id: int) -> float:
        """Calculate velocity score based on rating and download velocity."""
        async with get_db_context() as session:
            app = await self._get_app(session, app_id)
            if not app:
                return 0.0

            rating_velocity = self._calculate_rating_velocity(app)
            download_velocity = self._calculate_download_velocity(app)

            # Combine velocities (weighted)
            velocity_score = (rating_velocity * 0.6 + download_velocity * 0.4) * 100

            return min(100.0, max(0.0, velocity_score))

    async def _calculate_engagement_score(self, app_id: int) -> float:
        """Calculate engagement score based on user activity."""
        async with get_db_context() as session:
            app = await self._get_app(session, app_id)
            if not app:
                return 0.0

            if app.engagement_score:
                return min(100.0, app.engagement_score)

            # Estimate from available data
            engagement_score = 50.0

            # Higher rating suggests better engagement
            if app.rating:
                if app.rating >= 4.5:
                    engagement_score += 20
                elif app.rating >= 4.0:
                    engagement_score += 10
                elif app.rating < 3.0:
                    engagement_score -= 20

            # Recent ratings indicate active engagement
            if app.current_rating_count and app.rating_count:
                recent_ratio = app.current_rating_count / max(1, app.rating_count)
                if recent_ratio > 0.2:  # >20% recent ratings
                    engagement_score += 15

            return min(100.0, max(0.0, engagement_score))

    async def _calculate_shareability_score(self, app_id: int) -> float:
        """Calculate shareability score based on app characteristics."""
        async with get_db_context() as session:
            app = await self._get_app(session, app_id)
            if not app:
                return 0.0

            shareability_score = 50.0
            description = app.description or ""
            desc_lower = description.lower()

            # Social and communication apps are highly shareable
            social_keywords = [
                "social",
                "share",
                "connect",
                "community",
                "network",
                "chat",
                "messaging",
            ]
            for keyword in social_keywords:
                if keyword in desc_lower:
                    shareability_score += 10
                    break

            # Entertainment and gaming apps have high shareability
            entertainment_keywords = [
                "game",
                "fun",
                "play",
                "entertainment",
                "photo",
                "video",
                "music",
            ]
            for keyword in entertainment_keywords:
                if keyword in desc_lower:
                    shareability_score += 8
                    break

            # Utility apps that solve specific problems can be viral
            utility_keywords = [
                "productivity",
                "tool",
                "utility",
                "helper",
                "assistant",
                "organize",
            ]
            for keyword in utility_keywords:
                if keyword in desc_lower:
                    shareability_score += 5
                    break

            # Free apps have higher viral potential
            if app.price == 0:
                shareability_score += 15
            elif app.price and app.price < 5:
                shareability_score += 5

            return min(100.0, max(0.0, shareability_score))

    async def _calculate_timing_score(self, app_id: int) -> float:
        """Calculate timing score based on seasonality and trends."""
        async with get_db_context() as session:
            app = await self._get_app(session, app_id)
            if not app:
                return 0.0

            timing_score = 50.0

            # New releases have better timing
            if app.is_new_release:
                timing_score += 25

            # Currently trending
            if app.is_rising:
                timing_score += 20
            elif app.trend_direction == "up":
                timing_score += 15
            elif app.trend_direction == "down":
                timing_score -= 10

            # Seasonal opportunity
            if app.seasonal_opportunity_score:
                timing_score += app.seasonal_opportunity_score * 0.3

            return min(100.0, max(0.0, timing_score))

    def _detect_rating_spike(self, app: AppStoreApp) -> Dict[str, Any]:
        """Detect unusual rating velocity spike."""
        rating_velocity = self._calculate_rating_velocity(app)

        # Define spike threshold (ratings per day)
        spike_threshold = 50

        detected = rating_velocity > spike_threshold
        confidence = min(1.0, rating_velocity / 200.0) if detected else 0.0

        return {
            "detected": detected,
            "confidence": confidence,
            "velocity": rating_velocity,
        }

    def _detect_download_acceleration(self, app: AppStoreApp) -> Dict[str, Any]:
        """Detect accelerating download growth."""
        download_velocity = self._calculate_download_velocity(app)

        # Acceleration threshold
        accel_threshold = 1000  # downloads per day acceleration

        detected = download_velocity > accel_threshold
        confidence = min(1.0, download_velocity / 5000.0) if detected else 0.0

        return {
            "detected": detected,
            "confidence": confidence,
            "velocity": download_velocity,
        }

    def _detect_social_buzz(self, app: AppStoreApp) -> Dict[str, Any]:
        """Detect social media buzz indicators."""
        # Check for keywords indicating social sharing
        description = app.description or ""
        desc_lower = description.lower()

        buzz_keywords = [
            "viral",
            "trending",
            "sharing",
            "social",
            "community",
            "popular",
        ]
        buzz_count = sum(1 for keyword in buzz_keywords if keyword in desc_lower)

        detected = buzz_count >= 2
        confidence = min(1.0, buzz_count / 4.0)

        return {
            "detected": detected,
            "confidence": confidence,
            "keywords_found": buzz_count,
        }

    def _detect_media_mentions(self, app: AppStoreApp) -> Dict[str, Any]:
        """Detect potential media mentions."""
        # High rating count with recent spike suggests media attention
        if app.rating_count and app.rating_count > 10000:
            recent_ratio = app.current_rating_count / max(1, app.rating_count)
            detected = recent_ratio > 0.15  # >15% recent ratings
            confidence = min(1.0, recent_ratio)
        else:
            detected = False
            confidence = 0.0

        return {"detected": detected, "confidence": confidence}

    def _detect_category_breakthrough(self, app: AppStoreApp) -> Dict[str, Any]:
        """Detect app breaking through in its category."""
        # High rating in competitive category
        if app.rating and app.rating >= 4.5:
            # Check if category is competitive (high app count)
            if app.category and app.category.app_count > 1000:
                detected = True
                confidence = 0.7
            else:
                detected = True
                confidence = 0.4
        else:
            detected = False
            confidence = 0.0

        return {"detected": detected, "confidence": confidence}

    def _estimate_hours_to_viral(self, confidence: float, signal_count: int) -> int:
        """Estimate hours until viral breakout."""
        if confidence < 0.5:
            return 999  # Not going viral
        elif confidence < 0.7:
            return 72  # 3 days
        elif confidence < 0.85:
            return 48  # 2 days
        else:
            return 24  # 1 day

    def _get_recommended_actions(
        self, confidence: float, signals: List[str]
    ) -> List[str]:
        """Get recommended actions based on viral signals."""
        actions = ["Monitor closely"]

        if confidence > 0.7:
            actions.extend(["Prepare marketing push", "Check server capacity"])

        if "rating_spike" in signals:
            actions.append("Engage with new reviewers")

        if "download_acceleration" in signals:
            actions.append("Ensure app stability under load")

        if "social_buzz" in signals:
            actions.append("Amplify social media presence")

        if "media_mention" in signals:
            actions.append("Prepare media response strategy")

        if len(set(signals) & {"category_breakthrough", "media_mention"}):
            actions.append("Consider feature announcements")

        return actions

    def _calculate_urgency(self, early_viral: Dict[str, Any]) -> float:
        """Calculate urgency score for viral alerts."""
        base_urgency = early_viral["confidence"]

        # Higher urgency if less time to viral
        if early_viral["hours_to_viral"] < 24:
            base_urgency += 0.2
        elif early_viral["hours_to_viral"] < 48:
            base_urgency += 0.1

        # Higher urgency with more signals
        signal_bonus = min(0.2, len(early_viral["signals_detected"]) * 0.05)

        return min(1.0, base_urgency + signal_bonus)

    def _calculate_rating_velocity(self, app: AppStoreApp) -> float:
        """Calculate rating velocity (new ratings per day)."""
        if not app.current_rating_count or not app.age_in_days:
            return 0.0

        # Estimate recent ratings over last 30 days
        days = min(30, app.age_in_days)
        return app.current_rating_count / max(1, days)

    def _calculate_download_velocity(self, app: AppStoreApp) -> float:
        """Calculate download velocity (downloads per day)."""
        if not app.download_estimate or not app.age_in_days:
            return 0.0

        days = max(1, app.age_in_days)
        return app.download_estimate / days

    def _calculate_engagement_velocity(self, app: AppStoreApp) -> float:
        """Calculate engagement velocity."""
        if not app.active_user_estimate or not app.download_estimate:
            return 0.0

        return app.active_user_estimate / max(1, app.download_estimate)

    def _calculate_social_sharing_potential(self, app: AppStoreApp) -> float:
        """Calculate social sharing potential (0-100)."""
        base_score = 50.0

        description = app.description or ""
        desc_lower = description.lower()

        # Check for sharing-related keywords
        sharing_keywords = [
            "share",
            "social",
            "connect",
            "community",
            "invite",
            "friend",
        ]
        for keyword in sharing_keywords:
            if keyword in desc_lower:
                base_score += 10

        # Free apps have higher sharing potential
        if app.price == 0:
            base_score += 20

        return min(100.0, max(0.0, base_score))

    def _calculate_network_effects_score(self, app: AppStoreApp) -> float:
        """Calculate network effects potential."""
        base_score = 50.0

        # Apps with user interaction have network effects
        if app.category:
            high_network_categories = ["Social Networking", "Communication", "Games"]
            if app.category.name in high_network_categories:
                base_score += 30

        return min(100.0, max(0.0, base_score))

    def _calculate_viral_score_trend(self, history: List[Dict]) -> str:
        """Calculate viral score trend direction."""
        if len(history) < 2:
            return "stable"

        recent_scores = [h["viral_score"] for h in history[-7:]]
        older_scores = (
            [h["viral_score"] for h in history[-14:-7]]
            if len(history) >= 14
            else recent_scores
        )

        recent_avg = sum(recent_scores) / len(recent_scores)
        older_avg = sum(older_scores) / len(older_scores)

        diff = recent_avg - older_avg

        if diff > 5:
            return "rising"
        elif diff < -5:
            return "falling"
        else:
            return "stable"

    def _calculate_viral_growth_rate(self, history: List[Dict]) -> float:
        """Calculate viral growth rate percentage."""
        if len(history) < 2:
            return 0.0

        oldest_score = history[0]["viral_score"]
        newest_score = history[-1]["viral_score"]

        if oldest_score == 0:
            return 0.0

        return ((newest_score - oldest_score) / oldest_score) * 100

    def _estimate_invitations_per_user(self, app: AppStoreApp) -> float:
        """Estimate number of invitations sent per user."""
        base_invitations = 1.0

        # Social apps: higher invitation rate
        if app.category and app.category.name == "Social Networking":
            base_invitations = 3.0
        # Games: moderate invitation rate
        elif app.category and "Games" in app.category.name:
            base_invitations = 2.0
        # Utility apps: lower invitation rate
        elif app.category and app.category.name == "Utilities":
            base_invitations = 0.5

        # Adjust based on engagement
        if app.engagement_score and app.engagement_score > 70:
            base_invitations *= 1.5

        return base_invitations

    def _estimate_conversion_rate(self, app: AppStoreApp) -> float:
        """Estimate conversion rate of invitations."""
        base_rate = 0.1  # 10% base conversion

        # Higher rating = higher conversion
        if app.rating:
            if app.rating >= 4.5:
                base_rate = 0.25
            elif app.rating >= 4.0:
                base_rate = 0.20
            elif app.rating < 3.5:
                base_rate = 0.05

        # Free apps have higher conversion
        if app.price == 0:
            base_rate *= 1.5

        return min(1.0, base_rate)

    def _empty_viral_signal(self) -> Dict[str, Any]:
        """Return empty viral signal for missing apps."""
        return {
            "is_early_viral": False,
            "signals_detected": [],
            "confidence": 0.0,
            "hours_to_viral": 999,
            "recommended_actions": [],
            "viral_score": 0.0,
            "k_factor": 0.0,
        }

    async def _get_app(
        self, session: AsyncSession, app_id: int
    ) -> Optional[AppStoreApp]:
        """Get app with category loaded."""
        from sqlalchemy.orm import selectinload

        query = (
            select(AppStoreApp)
            .options(selectinload(AppStoreApp.category))
            .where(AppStoreApp.id == app_id)
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def _get_viral_history(
        self, session: AsyncSession, app_id: int, days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get viral history for an app."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        query = (
            select(AppViralHistory)
            .where(
                AppViralHistory.app_id == app_id,
                AppViralHistory.recorded_at >= cutoff_date,
            )
            .order_by(AppViralHistory.recorded_at)
        )

        result = await session.execute(query)
        history = result.scalars().all()

        return [
            {
                "viral_score": h.viral_score,
                "velocity": h.velocity,
                "coefficient": h.coefficient,
                "recorded_at": h.recorded_at.isoformat(),
            }
            for h in history
        ]


# Global service instance
viral_detection_service = ViralDetectionService()
