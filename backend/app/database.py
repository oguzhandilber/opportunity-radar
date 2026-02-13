"""Database connection and session management."""

from contextlib import asynccontextmanager
from datetime import datetime, timezone


def utc_now():
    return datetime.now(timezone.utc)


from typing import AsyncGenerator

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy import create_engine

from app.config import get_settings

settings = get_settings()

# Async engine for app with connection pooling
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Sync engine for migrations (Alembic)
sync_engine = create_engine(
    settings.database_sync_url,
    echo=settings.debug,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class RawPost(Base):
    """Raw posts scraped from all platforms."""

    __tablename__ = "raw_posts"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(50), nullable=False, index=True)
    external_id = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    author = Column(String(255))
    url = Column(Text)
    engagement = Column(Integer, default=0)
    # Timestamps
    created_at = Column(DateTime, default=utc_now, index=True)
    scraped_at = Column(DateTime, default=utc_now)

    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_source_external_id"),
        Index("ix_raw_posts_created", "created_at"),
    )

    # Relationship to opportunity
    opportunity = relationship("Opportunity", back_populates="raw_post", uselist=False)


class Opportunity(Base):
    """Analyzed opportunities derived from raw posts."""

    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True, index=True)
    raw_post_id = Column(Integer, ForeignKey("raw_posts.id"), nullable=False)

    # Basic info
    title = Column(String(500), nullable=False)
    summary = Column(Text)

    # Classification
    product_type = Column(String(100))
    sector = Column(String(100))
    business_model = Column(String(100))

    # Scores (1-10)
    demand_score = Column(Float)
    market_score = Column(Float)
    feasibility_score = Column(Float)
    revenue_score = Column(Float)
    total_score = Column(Float, index=True)
    confidence = Column(Float)

    # Enrichment
    competitors = Column(JSON)
    suggested_features = Column(JSON)
    go_to_market = Column(Text)

    # Payment Intent Analysis (Pivot 3)
    payment_signal_tier = Column(Integer)
    payment_signal_strength = Column(Float)
    mentioned_prices = Column(JSON)
    monthly_price_estimate = Column(Float)
    competitor_mentions = Column(JSON)
    churning_from = Column(JSON)
    purchase_journey_stage = Column(String(50))
    journey_confidence = Column(Float)
    revenue_potential_score = Column(Float)

    # Historical Success Validation (Pivot 4)
    matched_patterns = Column(JSON)
    pattern_match_score = Column(Float)
    success_prediction = Column(Float)
    similar_successes = Column(JSON)
    success_factors = Column(JSON)
    prediction_confidence = Column(Float)
    risk_level = Column(String(20))

    # Niche Focus (Pivot 2)
    detected_niches = Column(JSON)
    primary_niche = Column(String(50), index=True)
    niche_fit_score = Column(Float)
    niche_scores = Column(JSON)

    # Status
    status = Column(String(50), default="new", index=True)
    notes = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=utc_now, index=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationship to raw post
    raw_post = relationship("RawPost", back_populates="opportunity")

    # Relationship to validation experiments
    validation_experiments = relationship(
        "ValidationExperiment",
        back_populates="opportunity",
        cascade="all, delete-orphan",
    )

    # Relationship to validation tracking (Pivot 5)
    validation_trackers = relationship(
        "ValidationTracker", back_populates="opportunity", cascade="all, delete-orphan"
    )

    # No additional __table_args__ needed - indexes defined inline


class ValidationExperiment(Base):
    """Validation experiments for opportunities."""

    __tablename__ = "validation_experiments"

    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(
        Integer, ForeignKey("opportunities.id"), nullable=False, index=True
    )

    # Experiment details
    experiment_type = Column(String(50), nullable=False)
    hypothesis = Column(Text)
    target_metric = Column(String(100))
    status = Column(String(50), default="draft", index=True)

    # Results data (JSON)
    results = Column(JSON)

    # Landing page content (if applicable)
    landing_page_html = Column(Text)
    landing_page_url = Column(String(500))

    # Timestamps
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Relationship to opportunity
    opportunity = relationship("Opportunity", back_populates="validation_experiments")


class ValidationTracker(Base):
    """Validation tracking for opportunities (Pivot 5)."""

    __tablename__ = "validation_trackers"

    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(
        Integer, ForeignKey("opportunities.id"), nullable=False, index=True
    )

    # Tool configuration
    tool_type = Column(String(50), nullable=False)
    status = Column(String(50), default="planned", index=True)

    # Configuration (tool-specific settings stored as JSON)
    config = Column(JSON)

    # Results
    results = Column(JSON)
    simulated_results = Column(JSON)
    is_simulated = Column(Integer, default=0)

    # Metadata
    notes = Column(Text)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Relationship to opportunity
    opportunity = relationship("Opportunity", back_populates="validation_trackers")


class Setting(Base):
    """Application settings stored in database."""

    __tablename__ = "settings"

    key = Column(String(255), primary_key=True)
    value = Column(JSON)


# User and Workspace models for SaaS
class User(Base):
    """User accounts for multi-tenant SaaS."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    email_verification_token = Column(String(255))
    password_reset_token = Column(String(255))
    password_reset_expires = Column(DateTime)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Stripe customer ID
    stripe_customer_id = Column(String(100))

    # Relationships
    subscriptions = relationship(
        "Subscription", back_populates="user", cascade="all, delete-orphan"
    )
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan")
    saved_searches = relationship(
        "SavedSearch", back_populates="user", cascade="all, delete-orphan"
    )
    app_store_saved_searches = relationship(
        "AppStoreSavedSearch", back_populates="user", cascade="all, delete-orphan"
    )


class Workspace(Base):
    """Workspaces for team collaboration."""

    __tablename__ = "workspaces"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    subscriptions = relationship("Subscription", back_populates="workspace")
    integrations = relationship(
        "Integration", back_populates="workspace", cascade="all, delete-orphan"
    )


class Subscription(Base):
    """User subscriptions for SaaS tiers."""

    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    workspace_id = Column(
        Integer, ForeignKey("workspaces.id"), nullable=False, index=True
    )

    # Plan details
    plan = Column(String(50), default="free")  # free, pro, team
    status = Column(String(50), default="active")

    # Stripe integration
    stripe_customer_id = Column(String(100))
    stripe_subscription_id = Column(String(100))

    # Billing period
    current_period_start = Column(DateTime)
    current_period_end = Column(DateTime)
    cancel_at_period_end = Column(Boolean, default=False)

    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    user = relationship("User", back_populates="subscriptions")
    workspace = relationship("Workspace", back_populates="subscriptions")


class Alert(Base):
    """User alerts for new opportunities."""

    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255))

    # Alert conditions
    min_total_score = Column(Float)
    sectors = Column(JSON)
    product_types = Column(JSON)
    keywords = Column(JSON)

    # Notification channels
    email_enabled = Column(Boolean, default=True)
    slack_webhook = Column(String(500))

    last_alert_at = Column(DateTime)
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    user = relationship("User", back_populates="alerts")


class SavedSearch(Base):
    """Saved search filters for users."""

    __tablename__ = "saved_searches"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255))

    # Search criteria
    sectors = Column(JSON)
    product_types = Column(JSON)
    min_score = Column(Float)
    keywords = Column(JSON)
    source = Column(String(50))

    # Results tracking
    total_matches = Column(Integer, default=0)
    new_matches_today = Column(Integer, default=0)
    last_viewed_at = Column(DateTime)

    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    user = relationship("User", back_populates="saved_searches")


class OpportunityMetricsHistory(Base):
    """Historical metrics tracking for opportunities over time."""

    __tablename__ = "opportunity_metrics_history"

    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(
        Integer, ForeignKey("opportunities.id"), nullable=False, index=True
    )

    # Scores at this point in time
    total_score = Column(Float)
    demand_score = Column(Float)
    market_score = Column(Float)
    feasibility_score = Column(Float)
    revenue_score = Column(Float)

    # Engagement metrics
    mention_count = Column(Integer, default=0)
    avg_sentiment = Column(Float)

    # Trend indicators
    momentum_score = Column(Float)  # Rate of change
    trend_direction = Column(String(20))  # up, down, stable

    # Metadata
    recorded_at = Column(DateTime, default=utc_now, index=True)
    period = Column(String(20), default="daily")  # daily, weekly, monthly

    __table_args__ = (
        Index("ix_metrics_history_opportunity_date", "opportunity_id", "recorded_at"),
    )


class Integration(Base):
    """Third-party integrations for workspaces."""

    __tablename__ = "integrations"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(
        Integer, ForeignKey("workspaces.id"), nullable=False, index=True
    )

    type = Column(String(50))  # slack, discord, notion, airtable
    name = Column(String(255))
    webhook_url = Column(String(500))
    config = Column(JSON)  # Additional configuration
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    workspace = relationship("Workspace", back_populates="integrations")


async def init_db() -> None:
    """Initialize database tables."""
    async with engine.begin() as conn:
        # Skip PostgreSQL extensions that may not be available
        # await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
        # await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "pg_trgm"'))
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for database session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
