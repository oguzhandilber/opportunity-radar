"""App Store models for scraped iOS applications."""

from datetime import datetime, timezone


def utc_now():
    return datetime.now(timezone.utc)
    return datetime.now(timezone.utc)


from typing import List, Optional
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    JSON,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base


# App Store Categories (Top 15 Non-Game Categories)
APP_STORE_CATEGORIES = [
    {"name": "Business", "apple_id": "6000"},
    {"name": "Productivity", "apple_id": "6002"},
    {"name": "Finance", "apple_id": "6015"},
    {"name": "Health & Fitness", "apple_id": "6013"},
    {"name": "Medical", "apple_id": "6014"},
    {"name": "Education", "apple_id": "6017"},
    {"name": "Food & Drink", "apple_id": "6023"},
    {"name": "Shopping", "apple_id": "6024"},
    {"name": "Social Networking", "apple_id": "6005"},
    {"name": "Sports", "apple_id": "6016"},
    {"name": "Music", "apple_id": "6011"},
    {"name": "Navigation", "apple_id": "6010"},
    {"name": "Utilities", "apple_id": "6002"},
    {"name": "Weather", "apple_id": "6001"},
    {"name": "Lifestyle", "apple_id": "6012"},
]

# Revenue benchmarks by category (monthly revenue estimate per 1000 downloads)
CATEGORY_REVENUE_BENCHMARKS = {
    "Business": 50.0,
    "Productivity": 30.0,
    "Finance": 80.0,
    "Health & Fitness": 45.0,
    "Medical": 100.0,
    "Education": 25.0,
    "Food & Drink": 20.0,
    "Shopping": 15.0,
    "Social Networking": 10.0,
    "Sports": 20.0,
    "Music": 25.0,
    "Navigation": 30.0,
    "Utilities": 5.0,
    "Weather": 3.0,
    "Lifestyle": 15.0,
}

# Complexity multipliers by category (higher = harder to build)
CATEGORY_COMPLEXITY = {
    "Business": 0.6,
    "Productivity": 0.5,
    "Finance": 0.9,
    "Health & Fitness": 0.7,
    "Medical": 0.95,
    "Education": 0.5,
    "Food & Drink": 0.6,
    "Shopping": 0.7,
    "Social Networking": 0.8,
    "Sports": 0.6,
    "Music": 0.75,
    "Navigation": 0.85,
    "Utilities": 0.4,
    "Weather": 0.6,
    "Lifestyle": 0.5,
}


class AppStoreCategory(Base):
    """App Store category definitions."""

    __tablename__ = "app_store_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    apple_id = Column(String(10), nullable=False, unique=True)

    # Metadata
    app_count = Column(Integer, default=0)
    total_downloads_estimate = Column(Integer, default=0)
    average_rating = Column(Float, default=0.0)
    revenue_benchmark = Column(Float, default=0.0)  # $ per 1000 downloads
    complexity_multiplier = Column(Float, default=0.5)

    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    apps = relationship("AppStoreApp", back_populates="category", lazy="dynamic")


class AppStoreApp(Base):
    """Scraped App Store application data."""

    __tablename__ = "app_store_apps"

    id = Column(Integer, primary_key=True, index=True)
    apple_app_id = Column(String(100), unique=True, nullable=False, index=True)

    # Basic Info
    name = Column(String(255), nullable=False)
    developer = Column(String(255))
    description = Column(Text)
    icon_url = Column(String(500))
    screenshot_urls = Column(JSON)  # List of screenshot URLs

    # Store Info
    category_id = Column(Integer, ForeignKey("app_store_categories.id"))
    app_store_url = Column(String(500))
    content_rating = Column(String(50))
    languages = Column(JSON)  # List of supported languages

    # Pricing & Metrics
    price = Column(Float, default=0.0)
    currency = Column(String(3), default="USD")
    rating = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)
    current_rating_count = Column(Integer, default=0)  # Recent ratings (30 days)

    # Release Info
    release_date = Column(DateTime)
    last_updated = Column(DateTime)
    age_in_days = Column(Integer, default=0)  # Days since release

    # Rising/New Indicators
    is_new_release = Column(Boolean, default=False)  # Released within 30 days
    is_rising = Column(Boolean, default=False)  # Velocity-based
    trend_direction = Column(String(20))  # up, down, stable

    # Engagement Metrics (Estimated)
    download_estimate = Column(Integer, default=0)
    active_user_estimate = Column(Integer, default=0)
    engagement_score = Column(Float, default=0.0)

    # Revenue Estimation Fields
    monthly_revenue_estimate = Column(Integer, default=0)
    yearly_revenue_estimate = Column(Integer, default=0)
    revenue_confidence = Column(Float, default=0.0)

    # Seasonal Analysis Fields
    seasonal_pattern = Column(JSON)  # {"peak_months": [], "events": [], "score": 0.0}
    seasonal_opportunity_score = Column(Float, default=0.0)

    # Viral Detection Fields
    viral_score = Column(Float, default=0.0)
    viral_velocity = Column(Float, default=0.0)
    viral_coefficient = Column(Float, default=0.0)  # K-factor
    early_viral_signal = Column(Boolean, default=False)

    # Trend Forecasting Fields
    forecast_score = Column(Float, default=0.0)
    forecast_trend = Column(String(20))  # rising, falling, stable
    forecast_confidence = Column(Float, default=0.0)
    forecast_7d = Column(JSON)  # {"prediction": "", "confidence": 0.0, "reasoning": ""}
    forecast_30d = Column(JSON)  # Same structure

    # Clone Recommendations Fields
    similar_apps = Column(JSON)  # [{"app_id": int, "similarity": float, "type": ""}]
    clone_opportunities = Column(
        JSON
    )  # [{"type": "", "description": "", "potential": ""}]

    # Timestamps
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
    scraped_at = Column(DateTime, default=utc_now)

    # Relationships
    category = relationship("AppStoreCategory", back_populates="apps")
    scores = relationship(
        "AppScore", back_populates="app", uselist=False, cascade="all, delete-orphan"
    )
    trend_history = relationship(
        "AppTrendHistory", back_populates="app", cascade="all, delete-orphan"
    )
    revenue_history = relationship(
        "AppRevenueHistory", back_populates="app", cascade="all, delete-orphan"
    )
    viral_history = relationship(
        "AppViralHistory", back_populates="app", cascade="all, delete-orphan"
    )
    forecasts = relationship(
        "AppForecast", back_populates="app", cascade="all, delete-orphan"
    )
    clone_recommendations_as_source = relationship(
        "AppCloneRecommendation",
        foreign_keys="AppCloneRecommendation.source_app_id",
        back_populates="source_app",
        cascade="all, delete-orphan",
    )
    clone_recommendations_as_target = relationship(
        "AppCloneRecommendation",
        foreign_keys="AppCloneRecommendation.target_app_id",
        back_populates="target_app",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_app_store_apps_category", "category_id"),
        Index("ix_app_store_apps_apple_id", "apple_app_id"),
        Index("ix_app_store_apps_rating", "rating"),
        Index("ix_app_store_apps_is_rising", "is_rising"),
        Index("ix_app_store_apps_is_new", "is_new_release"),
        Index("ix_app_store_apps_scraped_at", "scraped_at"),
        Index("ix_app_store_apps_monthly_revenue", "monthly_revenue_estimate"),
        Index("ix_app_store_apps_viral_score", "viral_score"),
        Index("ix_app_store_apps_seasonal_opportunity", "seasonal_opportunity_score"),
        Index("ix_app_store_apps_forecast_score", "forecast_score"),
    )


class AppScore(Base):
    """AI-generated scores for App Store opportunities."""

    __tablename__ = "app_scores"

    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(
        Integer, ForeignKey("app_store_apps.id"), nullable=False, unique=True
    )

    # Scoring Dimensions (0-100)
    build_ease_score = Column(Float, default=0.0)  # Lower complexity = higher score
    revenue_potential_score = Column(Float, default=0.0)
    market_opportunity_score = Column(Float, default=0.0)
    rising_score = Column(Float, default=0.0)  # Momentum-based
    total_opportunity_score = Column(Float, default=0.0)  # Weighted average

    # Scoring Factors (JSON for transparency)
    build_ease_factors = Column(JSON)  # {
    #   "technical_complexity": 0-1,
    #   "team_size_needed": "solo/small/medium",
    #   "estimated_mvp_weeks": int,
    #   "tech_stack_difficulty": 0-1
    # }
    revenue_factors = Column(JSON)  # {
    #   "price_point": float,
    #   "category_revenue_benchmark": float,
    #   "market_size": "small/medium/large",
    #   "monetization_clarity": 0-1
    # }
    market_factors = Column(JSON)  # {
    #   "competition_level": "low/medium/high",
    #   "market_growth": -1 to 1,
    #   "pain_point_intensity": 0-1,
    #   "differentiation_opportunity": 0-1
    # }
    rising_factors = Column(JSON)  # {
    #   "rating_velocity": float,
    #   "download_velocity": float,
    #   "trend_direction": "up/down/stable",
    #   "momentum_score": 0-100
    # }

    # AI Analysis
    confidence_score = Column(Float, default=0.0)  # 0-1
    analysis_text = Column(Text)  # AI-generated summary
    opportunity_summary = Column(Text)  # Brief opportunity note

    # Metadata
    scoring_model = Column(String(50), default="v1.0")
    scored_at = Column(DateTime, default=utc_now)

    # Relationships
    app = relationship("AppStoreApp", back_populates="scores")

    __table_args__ = (
        Index("ix_app_scores_total", "total_opportunity_score"),
        Index("ix_app_scores_rising", "rising_score"),
        Index("ix_app_scores_build_ease", "build_ease_score"),
    )


class AppTrendHistory(Base):
    """Historical trend data for App Store apps."""

    __tablename__ = "app_trend_history"

    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, ForeignKey("app_store_apps.id"), nullable=False)

    # Daily Metrics
    ranking = Column(Integer)
    category_ranking = Column(Integer)
    rating = Column(Float)
    rating_count = Column(Integer)
    rating_velocity = Column(Float, default=0.0)  # New ratings per day

    # Derived Metrics
    ranking_change = Column(Integer, default=0)  # Day-over-day
    rating_change = Column(Float, default=0.0)

    # Metadata
    recorded_at = Column(DateTime, default=utc_now)

    # Relationships
    app = relationship("AppStoreApp", back_populates="trend_history")

    __table_args__ = (Index("ix_app_trend_history_app_date", "app_id", "recorded_at"),)


class AppRevenueHistory(Base):
    """Historical revenue data for App Store apps."""

    __tablename__ = "app_revenue_history"

    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, ForeignKey("app_store_apps.id"), nullable=False)
    monthly_estimate = Column(Integer)
    yearly_estimate = Column(Integer)
    confidence = Column(Float)
    download_velocity = Column(Float)
    revenue_velocity = Column(Float)
    recorded_at = Column(DateTime, default=utc_now)

    # Relationships
    app = relationship("AppStoreApp", back_populates="revenue_history")

    __table_args__ = (
        Index("ix_app_revenue_history_app_date", "app_id", "recorded_at"),
        Index("ix_app_revenue_history_monthly", "monthly_estimate"),
        Index("ix_app_revenue_history_confidence", "confidence"),
    )


class AppViralHistory(Base):
    """Historical viral metrics for App Store apps."""

    __tablename__ = "app_viral_history"

    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, ForeignKey("app_store_apps.id"), nullable=False)
    viral_score = Column(Float)
    velocity = Column(Float)
    coefficient = Column(Float)
    signals_detected = Column(JSON)  # ["signal1", "signal2"]
    recorded_at = Column(DateTime, default=utc_now)

    # Relationships
    app = relationship("AppStoreApp", back_populates="viral_history")

    __table_args__ = (
        Index("ix_app_viral_history_app_date", "app_id", "recorded_at"),
        Index("ix_app_viral_history_score", "viral_score"),
        Index("ix_app_viral_history_velocity", "velocity"),
    )


class AppForecast(Base):
    """Trend forecasting data for App Store apps."""

    __tablename__ = "app_forecasts"

    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, ForeignKey("app_store_apps.id"), nullable=False)
    forecast_days = Column(Integer)  # 7, 30, 90
    predicted_trend = Column(String(20))  # rising, falling, stable
    confidence = Column(Float)
    reasoning = Column(Text)
    factors = Column(JSON)  # {"factor1": weight, ...}
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    app = relationship("AppStoreApp", back_populates="forecasts")

    __table_args__ = (
        Index("ix_app_forecasts_app_days", "app_id", "forecast_days"),
        Index("ix_app_forecasts_trend", "predicted_trend"),
        Index("ix_app_forecasts_confidence", "confidence"),
        Index("ix_app_forecasts_created_at", "created_at"),
    )


class AppCloneRecommendation(Base):
    """Clone opportunity recommendations for App Store apps."""

    __tablename__ = "app_clone_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    source_app_id = Column(Integer, ForeignKey("app_store_apps.id"), nullable=False)
    target_app_id = Column(
        Integer, ForeignKey("app_store_apps.id")
    )  # NULL for external
    recommendation_type = Column(
        String(50)
    )  # direct_clone, feature_clone, platform_clone
    similarity_score = Column(Float)
    description = Column(Text)
    opportunity_potential = Column(Float)
    suggested_improvements = Column(JSON)
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    source_app = relationship(
        "AppStoreApp",
        foreign_keys=[source_app_id],
        back_populates="clone_recommendations_as_source",
    )
    target_app = relationship(
        "AppStoreApp",
        foreign_keys=[target_app_id],
        back_populates="clone_recommendations_as_target",
    )

    __table_args__ = (
        Index("ix_app_clone_recommendations_source", "source_app_id"),
        Index("ix_app_clone_recommendations_target", "target_app_id"),
        Index("ix_app_clone_recommendations_type", "recommendation_type"),
        Index("ix_app_clone_recommendations_potential", "opportunity_potential"),
        Index("ix_app_clone_recommendations_similarity", "similarity_score"),
        Index("ix_app_clone_recommendations_created_at", "created_at"),
    )


class AppStoreSavedSearch(Base):
    __tablename__ = "app_store_saved_searches"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)

    category = Column(String(100))
    min_score = Column(Float)
    is_rising = Column(Boolean)
    is_new = Column(Boolean)
    price_range = Column(JSON)
    sort_by = Column(String(50))
    keywords = Column(JSON)

    notify_on_match = Column(Boolean, default=False)

    total_matches = Column(Integer, default=0)
    new_matches_today = Column(Integer, default=0)
    last_viewed_at = Column(DateTime)

    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("User", lazy="select")

    __table_args__ = (
        Index("ix_app_store_saved_searches_user", "user_id"),
        Index("ix_app_store_saved_searches_category", "category"),
        Index("ix_app_store_saved_searches_min_score", "min_score"),
        Index("ix_app_store_saved_searches_is_rising", "is_rising"),
        Index("ix_app_store_saved_searches_is_new", "is_new"),
        Index("ix_app_store_saved_searches_notify", "notify_on_match"),
        Index("ix_app_store_saved_searches_created_at", "created_at"),
    )


class UserProfile(Base):
    """User profile for storing user information including phone number for ElevenLabs calls."""

    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone_number = Column(String(20), nullable=True, index=True)  # E.164 format for ElevenLabs

    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    __table_args__ = (
        Index("ix_user_profiles_phone", "phone_number"),
    )
