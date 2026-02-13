"""Test script to run HN scraper and create opportunities."""

import asyncio
import sys
sys.path.insert(0, '.')

from app.database import init_db, get_db_context, RawPost, Opportunity
from app.scrapers.hackernews import HackerNewsScraper
from app.analyzers.pipeline import run_analysis_pipeline
from sqlalchemy import select, func


async def run_scrape_test():
    print("=" * 60)
    print("Running Live Scrape Test")
    print("=" * 60)

    # Initialize database
    await init_db()
    print("[1] Database initialized")

    # Run HN scraper
    print("\n[2] Scraping Hacker News...")
    hn_scraper = HackerNewsScraper()
    posts = await hn_scraper.scrape()
    print(f"    Found {len(posts)} posts from HN")

    # Save posts
    saved = await hn_scraper.save_posts(posts)
    print(f"    Saved {saved} new posts to database")

    # Show some posts
    if posts:
        print("\n    Sample posts:")
        for post in posts[:3]:
            print(f"    - {post.content[:80]}...")

    # Run analysis pipeline
    print("\n[3] Running analysis pipeline...")
    results = await run_analysis_pipeline()
    print(f"    Created {results.get('opportunities_created', 0)} opportunities")

    # Show opportunities
    async with get_db_context() as session:
        result = await session.execute(
            select(Opportunity).order_by(Opportunity.total_score.desc()).limit(5)
        )
        opportunities = result.scalars().all()

        if opportunities:
            print("\n[4] Top Opportunities:")
            for opp in opportunities:
                print(f"\n    Title: {opp.title[:60]}...")
                print(f"    Type: {opp.product_type} | Sector: {opp.sector}")
                print(f"    Score: {opp.total_score}")

        # Stats
        count_result = await session.execute(select(func.count(Opportunity.id)))
        total = count_result.scalar()
        print(f"\n[5] Total opportunities in database: {total}")

    print("\n" + "=" * 60)
    print("Scrape test completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_scrape_test())
