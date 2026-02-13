"""Clone Recommendations Engine.

Identifies and analyzes clone opportunities for App Store apps based on:
- Direct clones: Same category, different audience/geo
- Feature clones: Same features, different category
- Platform clones: Same app, different platform
- Upgrade clones: Better version opportunities

Uses AI analysis to assess similarity, market gaps, and opportunity scores.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.analyzers.ai_client import get_ai_client
from app.database import get_db_context
from app.models.app_store import (
    AppStoreApp,
    AppStoreCategory,
    AppScore,
    CATEGORY_REVENUE_BENCHMARKS,
    CATEGORY_COMPLEXITY,
)

logger = logging.getLogger(__name__)


class CloneRecommendationService:
    """AI-powered clone recommendation service for App Store apps."""

    def __init__(self):
        self.ai_client = get_ai_client()

    async def find_clone_opportunities(self, app_id: int) -> List[Dict[str, Any]]:
        """Find similar apps that could be cloned."""
        async with get_db_context() as session:
            app = await self._get_app_with_details(session, app_id)
            if not app:
                return []

            recommendations = []

            # Direct clones in same category
            direct_clones = await self._find_direct_clones(session, app)
            recommendations.extend(direct_clones)

            # Feature clones in different categories
            feature_clones = await self._find_feature_clones(session, app)
            recommendations.extend(feature_clones)

            # Platform opportunities
            platform_clones = await self._find_platform_clones(session, app)
            recommendations.extend(platform_clones)

            # Upgrade opportunities
            upgrade_clones = await self._find_upgrade_clones(session, app)
            recommendations.extend(upgrade_clones)

            # Sort by opportunity score
            recommendations.sort(key=lambda x: x["opportunity_score"], reverse=True)

            return recommendations[:10]  # Top 10 recommendations

    async def generate_clone_suggestions(self, app_id: int) -> List[Dict[str, Any]]:
        """Generate AI-powered clone suggestions."""
        async with get_db_context() as session:
            app = await self._get_app_with_details(session, app_id)
            if not app:
                return []

            prompt = f"""
            Analyze this app and suggest 5 clone opportunities:

            App: {app.name}
            Category: {app.category.name if app.category else "Unknown"}
            Description: {app.description[:500] if app.description else ""}
            Rating: {app.rating} ({app.rating_count} reviews)
            Price: ${app.price}
            Estimated Downloads: {app.download_estimate}

            Suggest clone opportunities across these types:
            1. Direct clone for different market/audience
            2. Feature clone in different category
            3. Platform clone (iOS->Android, etc.)
            4. Upgrade clone with improvements
            5. Niche clone for specific use case

            For each suggestion, provide:
            - type: clone type
            - description: brief description
            - target_market: who to target
            - key_improvements: list of improvements
            - opportunity_score: 1-100 score
            - estimated_effort: low/medium/high

            Respond with JSON array of suggestions.
            """

            try:
                result = await self.ai_client.complete_json(prompt)
                suggestions = result if isinstance(result, list) else []
                return self._validate_suggestions(suggestions)
            except Exception as e:
                logger.error(f"AI clone suggestions error: {e}")
                return []

    async def find_feature_clones(
        self, app_id: int, target_category: str
    ) -> List[Dict[str, Any]]:
        """Find apps with similar features in different categories."""
        async with get_db_context() as session:
            app = await self._get_app_with_details(session, app_id)
            if not app:
                return []

            # Get target category
            target_cat_query = select(AppStoreCategory).where(
                AppStoreCategory.name.ilike(f"%{target_category}%")
            )
            target_cat_result = await session.execute(target_cat_query)
            target_category = target_cat_result.scalar_one_or_none()

            if not target_category or target_category.id == app.category_id:
                return []

            # Find apps in target category with feature similarity
            similarity_prompt = f"""
            Compare features between:
            
            Original app: {app.name}
            Category: {app.category.name if app.category else "Unknown"}
            Description: {app.description[:300] if app.description else ""}
            
            Target category: {target_category.name}
            
            Find apps in {target_category.name} that share core features but solve different problems.
            Look for feature overlap in: functionality, UI patterns, user workflows, tech approach.

            For each match, provide:
            - app_id: database ID
            - similarity: 0-100 score
            - shared_features: list of shared features
            - differentiator: how they're used differently
            - opportunity_score: 1-100

            Respond with JSON array of matches.
            """

            try:
                # Get apps in target category for analysis
                target_apps_query = (
                    select(AppStoreApp)
                    .where(AppStoreApp.category_id == target_category.id)
                    .where(AppStoreApp.rating_count > 100)
                    .limit(20)
                )
                target_apps_result = await session.execute(target_apps_query)
                target_apps = target_apps_result.scalars().all()

                if not target_apps:
                    return []

                # Enhanced prompt with actual target apps
                enhanced_prompt = similarity_prompt + "\n\nTarget apps to analyze:\n"
                for target_app in target_apps:
                    enhanced_prompt += f"\nID: {target_app.id}, Name: {target_app.name}, Desc: {target_app.description[:200] if target_app.description else ''}\n"

                result = await self.ai_client.complete_json(enhanced_prompt)
                matches = result if isinstance(result, list) else []

                return [
                    {
                        "type": "feature_clone",
                        "similarity": match.get("similarity", 0),
                        "description": match.get("differentiator", ""),
                        "target_app_id": match.get("app_id"),
                        "shared_features": match.get("shared_features", []),
                        "opportunity_score": match.get("opportunity_score", 0),
                        "target_category": target_category.name,
                    }
                    for match in matches
                    if match.get("opportunity_score", 0) > 50
                ]
            except Exception as e:
                logger.error(f"Feature clone analysis error: {e}")
                return []

    async def find_platform_clones(self, app_id: int) -> List[Dict[str, Any]]:
        """Find opportunities to port to other platforms."""
        async with get_db_context() as session:
            app = await self._get_app_with_details(session, app_id)
            if not app:
                return []

            platform_opportunities = []

            # Check if app is iOS-only (most common case)
            if app.download_estimate and app.download_estimate > 10000:
                # High-performing iOS apps are good Android candidates
                platform_opportunities.append(
                    {
                        "type": "platform_clone",
                        "similarity": 100.0,
                        "description": f"Port successful iOS app to Android",
                        "target_app_id": None,
                        "platform": "Android",
                        "opportunity_score": self._calculate_platform_opportunity_score(
                            app, "Android"
                        ),
                        "estimated_downloads": int(
                            app.download_estimate * 0.7
                        ),  # Android typically 70% of iOS
                        "development_effort": "medium",
                    }
                )

            # Check for web app opportunity
            if app.rating and app.rating >= 4.0 and app.rating_count > 1000:
                platform_opportunities.append(
                    {
                        "type": "platform_clone",
                        "similarity": 100.0,
                        "description": f"Create web version for broader access",
                        "target_app_id": None,
                        "platform": "Web",
                        "opportunity_score": self._calculate_platform_opportunity_score(
                            app, "Web"
                        ),
                        "development_effort": "low",
                    }
                )

            # Check for desktop opportunity
            if app.category and app.category.name in [
                "Productivity",
                "Business",
                "Finance",
            ]:
                platform_opportunities.append(
                    {
                        "type": "platform_clone",
                        "similarity": 100.0,
                        "description": f"Desktop version for {app.category.name} users",
                        "target_app_id": None,
                        "platform": "Desktop",
                        "opportunity_score": self._calculate_platform_opportunity_score(
                            app, "Desktop"
                        ),
                        "development_effort": "high",
                    }
                )

            return sorted(
                platform_opportunities,
                key=lambda x: x["opportunity_score"],
                reverse=True,
            )

    async def analyze_market_gaps(self, app_id: int) -> List[Dict[str, Any]]:
        """Identify market gaps and opportunities."""
        async with get_db_context() as session:
            app = await self._get_app_with_details(session, app_id)
            if not app:
                return []

            gaps = []

            # Analyze category for gaps
            if app.category:
                category_gaps = await self._analyze_category_gaps(session, app)
                gaps.extend(category_gaps)

            # Analyze user reviews for pain points
            review_gaps = await self._analyze_review_gaps(session, app)
            gaps.extend(review_gaps)

            # Analyze missing features
            feature_gaps = await self._analyze_missing_features(session, app)
            gaps.extend(feature_gaps)

            return sorted(gaps, key=lambda x: x["opportunity_score"], reverse=True)

    async def _get_app_with_details(
        self, session: AsyncSession, app_id: int
    ) -> Optional[AppStoreApp]:
        """Fetch app with category and score data."""
        query = (
            select(AppStoreApp)
            .options(
                selectinload(AppStoreApp.category),
                selectinload(AppStoreApp.score),
            )
            .where(AppStoreApp.id == app_id)
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def _find_direct_clones(
        self, session: AsyncSession, app: AppStoreApp
    ) -> List[Dict[str, Any]]:
        """Find direct clone opportunities in same category."""
        if not app.category_id:
            return []

        # Find similar apps in same category
        query = (
            select(AppStoreApp)
            .where(AppStoreApp.category_id == app.category_id)
            .where(AppStoreApp.id != app.id)
            .where(AppStoreApp.rating_count > 100)
            .where(AppStoreApp.download_estimate > 1000)
            .order_by(AppStoreApp.download_estimate.desc())
            .limit(10)
        )

        result = await session.execute(query)
        similar_apps = result.scalars().all()

        clones = []
        for similar_app in similar_apps:
            similarity = self._calculate_app_similarity(app, similar_app)

            if similarity > 60:  # Only include highly similar apps
                clones.append(
                    {
                        "type": "direct_clone",
                        "similarity": similarity,
                        "description": f"Similar app with {similar_app.download_estimate:,} estimated downloads",
                        "target_app_id": similar_app.id,
                        "target_app_name": similar_app.name,
                        "opportunity_score": self._calculate_direct_clone_score(
                            app, similar_app
                        ),
                        "price_difference": (similar_app.price or 0) - (app.price or 0),
                        "rating_gap": (similar_app.rating or 0) - (app.rating or 0),
                    }
                )

        return sorted(clones, key=lambda x: x["opportunity_score"], reverse=True)

    async def _find_feature_clones(
        self, session: AsyncSession, app: AppStoreApp
    ) -> List[Dict[str, Any]]:
        """Find feature clone opportunities in different categories."""
        # Get all other categories
        categories_query = select(AppStoreCategory).where(
            AppStoreCategory.id != app.category_id
        )
        categories_result = await session.execute(categories_query)
        other_categories = categories_result.scalars().all()

        feature_clones = []

        for category in other_categories[:5]:  # Check top 5 categories
            # Find top apps in this category
            apps_query = (
                select(AppStoreApp)
                .where(AppStoreApp.category_id == category.id)
                .where(AppStoreApp.rating_count > 500)
                .order_by(AppStoreApp.rating_count.desc())
                .limit(3)
            )

            apps_result = await session.execute(apps_query)
            category_apps = apps_result.scalars().all()

            for category_app in category_apps:
                similarity = await self._calculate_feature_similarity(app, category_app)

                if similarity > 50:
                    feature_clones.append(
                        {
                            "type": "feature_clone",
                            "similarity": similarity,
                            "description": f"{app.name} features applied to {category.name}",
                            "target_app_id": category_app.id,
                            "target_app_name": category_app.name,
                            "target_category": category.name,
                            "opportunity_score": self._calculate_feature_clone_score(
                                app, category_app, category
                            ),
                        }
                    )

        return sorted(
            feature_clones, key=lambda x: x["opportunity_score"], reverse=True
        )[:5]

    async def _find_platform_clones(
        self, session: AsyncSession, app: AppStoreApp
    ) -> List[Dict[str, Any]]:
        """Find platform clone opportunities."""
        return await self.find_platform_clones(app.id)

    async def _find_upgrade_clones(
        self, session: AsyncSession, app: AppStoreApp
    ) -> List[Dict[str, Any]]:
        """Find upgrade clone opportunities."""
        # Analyze app for improvement opportunities
        improvement_prompt = f"""
        Analyze this app for upgrade opportunities:

        App: {app.name}
        Category: {app.category.name if app.category else "Unknown"}
        Description: {app.description[:500] if app.description else ""}
        Rating: {app.rating} ({app.rating_count} reviews)
        Price: ${app.price}
        Current Features: {app.description[:200] if app.description else ""}

        Identify 3-5 specific upgrade opportunities that could justify a "better version" clone.
        Focus on:
        - Missing modern features (dark mode, offline, etc.)
        - UI/UX improvements
        - Performance issues
        - Missing integrations
        - Limited functionality

        For each upgrade:
        - improvement: specific improvement
        - impact: high/medium/low impact
        - effort: low/medium/high effort
        - user_demand: evidence from reviews/market

        Respond with JSON array of upgrades.
        """

        try:
            result = await self.ai_client.complete_json(improvement_prompt)
            upgrades = result if isinstance(result, list) else []

            if not upgrades:
                return []

            # Calculate opportunity score based on improvements
            base_score = 50.0
            if app.rating and app.rating < 4.0:
                base_score += 20  # Poor rating = upgrade opportunity
            if app.rating_count and app.rating_count < 10000:
                base_score += 15  # Low competition

            high_impact_count = sum(1 for u in upgrades if u.get("impact") == "high")
            base_score += high_impact_count * 10

            opportunity_score = min(100, base_score)

            return [
                {
                    "type": "upgrade_clone",
                    "similarity": 65.0,  # Base similarity for upgrades
                    "description": f"Opportunity to build better version with {len(upgrades)} improvements",
                    "target_app_id": app.id,  # Upgrading the same app
                    "target_app_name": app.name,
                    "improvements": [u.get("improvement", "") for u in upgrades[:5]],
                    "opportunity_score": opportunity_score,
                    "estimated_effort": "medium" if len(upgrades) > 3 else "low",
                }
            ]
        except Exception as e:
            logger.error(f"Upgrade analysis error: {e}")
            return []

    def _calculate_app_similarity(self, app1: AppStoreApp, app2: AppStoreApp) -> float:
        """Calculate similarity between two apps."""
        similarity = 50.0  # Base similarity

        # Category similarity (already same for direct clones)
        if app1.category_id == app2.category_id:
            similarity += 20

        # Rating similarity
        if app1.rating and app2.rating:
            rating_diff = abs(app1.rating - app2.rating)
            similarity += max(0, 20 - rating_diff * 10)

        # Price similarity
        price1, price2 = app1.price or 0, app2.price or 0
        if price1 == 0 and price2 == 0:
            similarity += 15  # Both free
        elif price1 > 0 and price2 > 0:
            price_diff = abs(price1 - price2) / max(price1, price2, 1)
            similarity += max(0, 15 - price_diff * 15)

        # Description similarity (basic keyword overlap)
        if app1.description and app2.description:
            desc1_words = set(app1.description.lower().split())
            desc2_words = set(app2.description.lower().split())
            if desc1_words and desc2_words:
                overlap = len(desc1_words & desc2_words) / len(
                    desc1_words | desc2_words
                )
                similarity += overlap * 30

        return min(100, similarity)

    async def _calculate_feature_similarity(
        self, app1: AppStoreApp, app2: AppStoreApp
    ) -> float:
        """Calculate feature similarity between apps in different categories."""
        similarity_prompt = f"""
        Compare these two apps for feature similarity:

        App 1: {app1.name} ({app1.category.name if app1.category else "Unknown"})
        Description: {app1.description[:300] if app1.description else ""}

        App 2: {app2.name} ({app2.category.name if app2.category else "Unknown"})  
        Description: {app2.description[:300] if app2.description else ""}

        Focus on:
        - Core functionality overlap
        - User interaction patterns
        - Technical approaches
        - Problem-solving methods

        Respond with JSON:
        {{
            "similarity": 0-100,
            "shared_features": ["feature1", "feature2"],
            "key_differences": ["difference1", "difference2"]
        }}
        """

        try:
            result = await self.ai_client.complete_json(similarity_prompt)
            return result.get("similarity", 0)
        except Exception as e:
            logger.error(f"Feature similarity error: {e}")
            return 30.0  # Default low similarity

    def _calculate_direct_clone_score(
        self, original_app: AppStoreApp, clone_app: AppStoreApp
    ) -> float:
        """Calculate opportunity score for direct clone."""
        score = 50.0

        # Higher target app downloads = bigger opportunity
        if clone_app.download_estimate:
            if clone_app.download_estimate > 100000:
                score += 25
            elif clone_app.download_estimate > 10000:
                score += 15
            elif clone_app.download_estimate > 1000:
                score += 5

        # Original app has room for improvement
        if original_app.rating and original_app.rating < 4.0:
            score += 15
        if original_app.rating_count and original_app.rating_count < 5000:
            score += 10

        # Price opportunity
        if clone_app.price and clone_app.price > 10:
            score += 10

        return min(100, score)

    def _calculate_feature_clone_score(
        self,
        original_app: AppStoreApp,
        target_app: AppStoreApp,
        target_category: AppStoreCategory,
    ) -> float:
        """Calculate opportunity score for feature clone."""
        score = 50.0

        # Category revenue potential
        category_revenue = CATEGORY_REVENUE_BENCHMARKS.get(target_category.name, 20)
        if category_revenue > 50:
            score += 20
        elif category_revenue > 25:
            score += 10

        # Target app success
        if target_app.rating and target_app.rating > 4.0:
            score += 10
        if target_app.download_estimate and target_app.download_estimate > 10000:
            score += 10

        # Original app quality (indicates good features)
        if original_app.rating and original_app.rating > 4.2:
            score += 10

        return min(100, score)

    def _calculate_platform_opportunity_score(
        self, app: AppStoreApp, platform: str
    ) -> float:
        """Calculate opportunity score for platform clone."""
        score = 50.0

        # Base success on original app performance
        if app.download_estimate:
            if app.download_estimate > 100000:
                score += 20
            elif app.download_estimate > 10000:
                score += 10

        if app.rating and app.rating > 4.0:
            score += 15

        # Platform-specific factors
        platform_multipliers = {
            "Android": 1.2,  # Android has larger market
            "Web": 1.0,  # Neutral
            "Desktop": 0.8,  # Smaller but valuable
        }

        score *= platform_multipliers.get(platform, 1.0)

        return min(100, score)

    async def _analyze_category_gaps(
        self, session: AsyncSession, app: AppStoreApp
    ) -> List[Dict[str, Any]]:
        """Analyze category for market gaps."""
        if not app.category_id:
            return []

        # Get category stats
        category_stats_query = select(
            func.count(AppStoreApp.id).label("app_count"),
            func.avg(AppStoreApp.rating).label("avg_rating"),
            func.sum(AppStoreApp.download_estimate).label("total_downloads"),
        ).where(AppStoreApp.category_id == app.category_id)

        result = await session.execute(category_stats_query)
        stats = result.first()

        gaps = []

        # Low competition gap
        if stats.app_count < 50:
            gaps.append(
                {
                    "type": "market_gap",
                    "similarity": 0,
                    "description": f"Low competition in {app.category.name if app.category else 'category'} ({stats.app_count} apps)",
                    "target_app_id": None,
                    "opportunity_score": 70,
                    "gap_type": "low_competition",
                }
            )

        # Quality gap
        if stats.avg_rating and stats.avg_rating < 3.5:
            gaps.append(
                {
                    "type": "market_gap",
                    "similarity": 0,
                    "description": f"Low quality category ({stats.avg_rating:.1f} avg rating)",
                    "target_app_id": None,
                    "opportunity_score": 75,
                    "gap_type": "quality_gap",
                }
            )

        return gaps

    async def _analyze_review_gaps(
        self, session: AsyncSession, app: AppStoreApp
    ) -> List[Dict[str, Any]]:
        """Analyze reviews for pain points and gaps."""
        # This would require access to review data - simplified for now
        return []

    async def _analyze_missing_features(
        self, session: AsyncSession, app: AppStoreApp
    ) -> List[Dict[str, Any]]:
        """Analyze missing modern features."""
        missing_features = []

        # Check description for common modern features
        description = (app.description or "").lower()

        common_features = {
            "dark mode": "Dark mode support",
            "offline": "Offline functionality",
            "sync": "Cloud sync",
            "api": "API integration",
            "multi-platform": "Cross-platform support",
            "collaboration": "Collaboration features",
            "ai": "AI-powered features",
        }

        missing = [
            features
            for keyword, features in common_features.items()
            if keyword not in description
        ]

        if len(missing) >= 3:
            missing_features.append(
                {
                    "type": "feature_gap",
                    "similarity": 0,
                    "description": f"Missing {len(missing)} modern features",
                    "target_app_id": None,
                    "opportunity_score": 65,
                    "missing_features": missing[:5],
                }
            )

        return missing_features

    def _validate_suggestions(self, suggestions: List[Dict]) -> List[Dict]:
        """Validate and clean AI suggestions."""
        valid_suggestions = []

        required_fields = ["type", "description", "opportunity_score"]

        for suggestion in suggestions:
            if all(field in suggestion for field in required_fields):
                # Clean and normalize
                suggestion["opportunity_score"] = min(
                    100, max(1, suggestion.get("opportunity_score", 50))
                )
                suggestion["type"] = suggestion.get("type", "unknown")
                suggestion["description"] = suggestion.get("description", "")[:200]
                valid_suggestions.append(suggestion)

        return valid_suggestions


# Export service instance
clone_recommendation_service = CloneRecommendationService()
