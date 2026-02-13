"""Add niche focus fields to opportunities table.

This migration adds the Pivot 2 niche focus fields.
Run with: python -m alembic upgrade head
Or manually: python migration_add_niche_fields.py
"""

import asyncio
from sqlalchemy import text
from app.database import engine, get_db_context


async def add_niche_fields():
    """Add niche focus fields to opportunities table."""

    async with engine.begin() as conn:
        # Check if fields already exist
        result = await conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'opportunities'
            AND column_name = 'primary_niche'
        """))

        if result.fetchone():
            print("Niche fields already exist, skipping migration")
            return

        print("Adding niche focus fields...")

        # Add detected_niches (JSON)
        await conn.execute(text("""
            ALTER TABLE opportunities
            ADD COLUMN detected_niches JSON
        """))

        # Add primary_niche (String with index)
        await conn.execute(text("""
            ALTER TABLE opportunities
            ADD COLUMN primary_niche VARCHAR(50)
        """))

        # Add niche_fit_score (Float)
        await conn.execute(text("""
            ALTER TABLE opportunities
            ADD COLUMN niche_fit_score FLOAT
        """))

        # Add niche_scores (JSON)
        await conn.execute(text("""
            ALTER TABLE opportunities
            ADD COLUMN niche_scores JSON
        """))

        # Create index on primary_niche
        await conn.execute(text("""
            CREATE INDEX ix_opportunities_primary_niche
            ON opportunities (primary_niche)
        """))

        print("Successfully added niche focus fields!")
        print("Fields added:")
        print("  - detected_niches (JSON)")
        print("  - primary_niche (VARCHAR(50), indexed)")
        print("  - niche_fit_score (FLOAT)")
        print("  - niche_scores (JSON)")


async def main():
    """Run the migration."""
    try:
        await add_niche_fields()
        print("\nMigration completed successfully!")
    except Exception as e:
        print(f"\nMigration failed: {e}")
        print("\nIf using SQLite, the migration may fail due to ALTER TABLE limitations.")
        print("In that case, you'll need to recreate the database:")
        print("  1. Delete the database file")
        print("  2. Run: python -c 'import asyncio; from app.database import init_db; asyncio.run(init_db())'")
        raise


if __name__ == "__main__":
    asyncio.run(main())
