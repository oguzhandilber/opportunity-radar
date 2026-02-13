"""Initial migration

Revision ID: bf61ba7bb35e
Revises:
Create Date: 2026-01-27 14:22:55.245517

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bf61ba7bb35e'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - create initial tables."""
    # Create raw_posts table
    op.create_table(
        'raw_posts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('external_id', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('author', sa.String(length=255), nullable=True),
        sa.Column('url', sa.Text(), nullable=True),
        sa.Column('engagement', sa.Integer(), nullable=True, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('scraped_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('source', 'external_id', name='uq_source_external_id'),
    )
    op.create_index(op.f('ix_raw_posts_id'), 'raw_posts', ['id'], unique=False)
    op.create_index(op.f('ix_raw_posts_source'), 'raw_posts', ['source'], unique=False)

    # Create opportunities table
    op.create_table(
        'opportunities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('raw_post_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('product_type', sa.String(length=100), nullable=True),
        sa.Column('sector', sa.String(length=100), nullable=True),
        sa.Column('business_model', sa.String(length=100), nullable=True),
        sa.Column('demand_score', sa.Float(), nullable=True),
        sa.Column('market_score', sa.Float(), nullable=True),
        sa.Column('feasibility_score', sa.Float(), nullable=True),
        sa.Column('revenue_score', sa.Float(), nullable=True),
        sa.Column('total_score', sa.Float(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('competitors', sa.JSON(), nullable=True),
        sa.Column('suggested_features', sa.JSON(), nullable=True),
        sa.Column('go_to_market', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True, default='new'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['raw_post_id'], ['raw_posts.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_opportunities_id'), 'opportunities', ['id'], unique=False)
    op.create_index(op.f('ix_opportunities_status'), 'opportunities', ['status'], unique=False)

    # Create settings table
    op.create_table(
        'settings',
        sa.Column('key', sa.String(length=255), nullable=False),
        sa.Column('value', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('key'),
    )


def downgrade() -> None:
    """Downgrade schema - drop all tables."""
    op.drop_table('settings')
    op.drop_index(op.f('ix_opportunities_status'), table_name='opportunities')
    op.drop_index(op.f('ix_opportunities_id'), table_name='opportunities')
    op.drop_table('opportunities')
    op.drop_index(op.f('ix_raw_posts_source'), table_name='raw_posts')
    op.drop_index(op.f('ix_raw_posts_id'), table_name='raw_posts')
    op.drop_table('raw_posts')
