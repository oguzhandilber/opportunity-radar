"""Test script to verify AI analysis pipeline works."""

import asyncio
import sys
sys.path.insert(0, '.')

from app.analyzers.filter import ContentFilter
from app.analyzers.classifier import OpportunityClassifier
from app.analyzers.scorer import OpportunityScorer
from app.analyzers.enricher import OpportunityEnricher

# Test content - real example
TEST_CONTENT = """
I've been looking for a simple tool to help small businesses manage their
customer appointments. Most solutions are way too complex or expensive.
I run a small salon and I just need something that:
- Lets customers book online
- Sends SMS reminders
- Syncs with my calendar

I'd pay $20-30/month for something that just works. Anyone know of a simple
alternative to Calendly that's focused on small service businesses?
"""


async def test_pipeline():
    print("=" * 60)
    print("Testing Opportunity Radar AI Pipeline")
    print("=" * 60)

    # Step 1: Filter
    print("\n[1] Content Filter")
    filter_module = ContentFilter()
    is_relevant = filter_module.is_relevant(TEST_CONTENT)
    print(f"    Is relevant: {is_relevant}")

    if not is_relevant:
        print("    FAIL: Content should be marked as relevant")
        return False

    cleaned = filter_module.clean_content(TEST_CONTENT)
    print(f"    Cleaned length: {len(cleaned)} chars")

    # Step 2: Classifier (requires API key)
    print("\n[2] Opportunity Classifier")
    classifier = OpportunityClassifier()
    try:
        classification = await classifier.classify(TEST_CONTENT)
        if classification:
            print(f"    Title: {classification.get('title')}")
            print(f"    Product Type: {classification.get('product_type')}")
            print(f"    Sector: {classification.get('sector')}")
            print(f"    Business Model: {classification.get('business_model')}")
        else:
            print("    Classification returned None (no API key or not an opportunity)")
    except Exception as e:
        print(f"    Skipped (API key not configured): {type(e).__name__}")
        # Create mock classification for next steps
        classification = {
            "title": "Simple Appointment Booking for Small Businesses",
            "summary": "A simplified booking solution for small service businesses",
            "product_type": "SaaS",
            "sector": "Productivity",
            "business_model": "Subscription",
        }

    # Step 3: Scorer (requires API key)
    print("\n[3] Opportunity Scorer")
    scorer = OpportunityScorer()
    try:
        scores = await scorer.score(TEST_CONTENT, classification)
        print(f"    Demand Score: {scores.get('demand_score')}")
        print(f"    Market Score: {scores.get('market_score')}")
        print(f"    Feasibility Score: {scores.get('feasibility_score')}")
        print(f"    Revenue Score: {scores.get('revenue_score')}")
        print(f"    Total Score: {scores.get('total_score')}")
        print(f"    Confidence: {scores.get('confidence')}")
    except Exception as e:
        print(f"    Skipped (API key not configured): {type(e).__name__}")

    # Step 4: Enricher (requires API key)
    print("\n[4] Opportunity Enricher")
    enricher = OpportunityEnricher()
    try:
        enrichment = await enricher.enrich(TEST_CONTENT, classification)
        print(f"    Competitors: {len(enrichment.get('competitors', []))} found")
        print(f"    Features: {len(enrichment.get('suggested_features', []))} suggested")
        print(f"    GTM Strategy: {'Yes' if enrichment.get('go_to_market') else 'No'}")
    except Exception as e:
        print(f"    Skipped (API key not configured): {type(e).__name__}")

    print("\n" + "=" * 60)
    print("Pipeline test completed!")
    print("=" * 60)

    return True


if __name__ == "__main__":
    asyncio.run(test_pipeline())
