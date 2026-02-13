from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "bf61ba7bb35e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "app_store_saved_searches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("min_score", sa.Float(), nullable=True),
        sa.Column("is_rising", sa.Boolean(), nullable=True),
        sa.Column("is_new", sa.Boolean(), nullable=True),
        sa.Column("price_range", sa.JSON(), nullable=True),
        sa.Column("sort_by", sa.String(length=50), nullable=True),
        sa.Column("keywords", sa.JSON(), nullable=True),
        sa.Column("notify_on_match", sa.Boolean(), nullable=True, default=False),
        sa.Column("total_matches", sa.Integer(), nullable=True, default=0),
        sa.Column("new_matches_today", sa.Integer(), nullable=True, default=0),
        sa.Column("last_viewed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_app_store_saved_searches_id"),
        "app_store_saved_searches",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_app_store_saved_searches_user"),
        "app_store_saved_searches",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_app_store_saved_searches_category"),
        "app_store_saved_searches",
        ["category"],
        unique=False,
    )
    op.create_index(
        op.f("ix_app_store_saved_searches_min_score"),
        "app_store_saved_searches",
        ["min_score"],
        unique=False,
    )
    op.create_index(
        op.f("ix_app_store_saved_searches_is_rising"),
        "app_store_saved_searches",
        ["is_rising"],
        unique=False,
    )
    op.create_index(
        op.f("ix_app_store_saved_searches_is_new"),
        "app_store_saved_searches",
        ["is_new"],
        unique=False,
    )
    op.create_index(
        op.f("ix_app_store_saved_searches_notify"),
        "app_store_saved_searches",
        ["notify_on_match"],
        unique=False,
    )
    op.create_index(
        op.f("ix_app_store_saved_searches_created_at"),
        "app_store_saved_searches",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("app_store_saved_searches")
