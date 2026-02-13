"""Analysis pipeline - orchestrates AI-powered analysis."""

import logging

from app.analyzers.filter import ContentFilter
from app.analyzers.ai_client import get_ai_client
from app.analyzers.payment_signals import PaymentSignalDetector
from app.analyzers.price_extractor import PriceExtractor
from app.analyzers.competitor_extractor import CompetitorExtractor
from app.analyzers.journey_classifier import JourneyClassifier
from app.analyzers.pattern_matcher import PatternMatcher
from app.analyzers.success_predictor import SuccessPredictor
from app.analyzers.niche_detector import NicheDetector
from app.analyzers.niche_scorer import NicheScorer
from app.analyzers.deduplicator import ContentDeduplicator, find_duplicate_opportunities
from app.database import RawPost, Opportunity, get_db_context
from sqlalchemy import select

logger = logging.getLogger(__name__)


async def run_analysis_pipeline() -> dict:
    """Run the full AI analysis pipeline on unprocessed posts."""
    filter_module = ContentFilter()
    ai_client = get_ai_client()

    # Payment intent analyzers (Pivot 3)
    payment_detector = PaymentSignalDetector()
    price_extractor = PriceExtractor()
    competitor_extractor = CompetitorExtractor()
    journey_classifier = JourneyClassifier()

    # Success validation (Pivot 4)
    pattern_matcher = PatternMatcher()
    success_predictor = SuccessPredictor()

    # Niche focus (Pivot 2)
    niche_detector = NicheDetector()
    niche_scorer = NicheScorer()

    opportunities_created = 0
    skipped = 0
    duplicates = 0
    errors = []

    async with get_db_context() as session:
        # Get posts that don't have opportunities yet
        subquery = select(Opportunity.raw_post_id)
        query = select(RawPost).where(~RawPost.id.in_(subquery))
        result = await session.execute(query)
        unprocessed_posts = result.scalars().all()

        logger.info(f"Processing {len(unprocessed_posts)} posts with AI...")

        # Build deduplication cache from existing opportunities
        existing_query = (
            select(Opportunity.id, Opportunity.title, Opportunity.summary)
            .order_by(Opportunity.created_at.desc())
            .limit(500)
        )  # Check against last 500 opportunities
        existing_result = await session.execute(existing_query)
        existing_opportunities = existing_result.all()

        deduplicator = ContentDeduplicator(similarity_threshold=0.35)
        for opp_id, title, summary in existing_opportunities:
            combined = f"{title or ''} {summary or ''}"
            deduplicator.add_to_cache(opp_id, combined)

        for i, post in enumerate(unprocessed_posts):
            try:
                # Defensive: ensure post has content attribute (not a dict)
                if not hasattr(post, "content") or content is None:
                    logger.warning(
                        f"Skipping post {getattr(post, 'id', 'unknown')}: no content attribute"
                    )
                    skipped += 1
                    continue

                # Ensure content is a string, not a dict
                if isinstance(content, dict):
                    logger.warning(
                        f"Post {getattr(post, 'id', 'unknown')}: content is dict, skipping"
                    )
                    skipped += 1
                    continue

                content = str(content) if content else ""

                # Step 1: Quick filter (no AI needed)
                if not filter_module.is_relevant(content):
                    skipped += 1
                    continue

                # Step 1.5: Check for duplicate/similar opportunities
                similar = deduplicator.find_similar(content)
                if similar.is_similar:
                    logger.debug(
                        f"Skipping duplicate: similarity={similar.similarity_score:.2f} "
                        f"with opportunity #{similar.matched_id}"
                    )
                    duplicates += 1
                    continue

                logger.info(
                    f"Analyzing post {i + 1}/{len(unprocessed_posts)}: {content[:50]}..."
                )

                # Step 2: Payment Intent Analysis (Pivot 3 - no AI needed)
                payment_result = payment_detector.detect(content)
                price_result = price_extractor.extract(content)
                competitor_result = competitor_extractor.extract(content)
                journey_result = journey_classifier.classify(content)

                # Calculate revenue potential score
                revenue_potential = _calculate_revenue_potential(
                    payment_result, price_result, competitor_result, journey_result
                )

                # Step 3: Success Pattern Matching (Pivot 4 - no AI needed)
                pattern_result = pattern_matcher.match(
                    content,
                    category_hint=None,  # Will be updated after AI analysis
                )

                # Success Prediction using all signals
                success_prediction = success_predictor.predict(
                    content,
                    pre_computed={
                        "pattern_result": pattern_result,
                        "payment_result": payment_result,
                        "competitor_result": competitor_result,
                        "journey_result": journey_result,
                    },
                )

                # Step 4: AI Analysis (single call for everything)
                # All AI clients now support analyze_opportunity via the common interface
                analysis = await ai_client.analyze_opportunity(
                    content=content, source=post.source
                )

                # Check if it's actually an opportunity
                if not analysis.get("is_opportunity", True):
                    skipped += 1
                    continue

                # Step 5: Niche Detection and Scoring (Pivot 2)
                niche_result = niche_detector.detect_from_opportunity_data(
                    title=analysis.get("title", content[:100]),
                    summary=analysis.get("summary", ""),
                    sector=analysis.get("sector"),
                    product_type=analysis.get("product_type"),
                )

                # Score for detected niche(s)
                niche_scores_dict = {}
                primary_niche_id = None
                niche_fit_score = 0.0

                if niche_result.primary_niche:
                    primary_niche_id = niche_result.primary_niche.niche_id

                    # Prepare opportunity data for scoring
                    opp_data = {
                        "demand_score": analysis.get("demand_score", 5),
                        "market_score": analysis.get("market_score", 5),
                        "revenue_score": analysis.get("revenue_score", 5),
                        "feasibility_score": analysis.get("feasibility_score", 5),
                        "business_model": analysis.get("business_model", ""),
                        "sector": analysis.get("sector", ""),
                        "payment_signal_tier": payment_result.tier,
                        "revenue_potential_score": revenue_potential,
                        "competitors": analysis.get("competitors", []),
                        "monthly_price_estimate": price_result.monthly_equivalent,
                        "success_prediction": success_prediction.success_likelihood,
                    }

                    niche_scores_dict = niche_scorer.score(
                        niche_result,
                        opp_data,
                        primary_only=False,  # Score all significant niches
                    )

                    # Get primary niche fit score
                    if primary_niche_id in niche_scores_dict:
                        niche_fit_score = niche_scores_dict[
                            primary_niche_id
                        ].niche_fit_score

                # Build competitors list
                competitors = analysis.get("competitors", [])
                if isinstance(competitors, list) and competitors:
                    if isinstance(competitors[0], str):
                        # Convert string list to proper format
                        competitors = [
                            {"name": c, "url": "", "notes": ""} for c in competitors
                        ]

                # Build features list
                features = analysis.get(
                    "key_features", analysis.get("suggested_features", [])
                )
                if isinstance(features, list) and features:
                    if isinstance(features[0], str):
                        # Convert string list to proper format
                        features = [
                            {
                                "feature": f,
                                "priority": "high" if i < 3 else "medium",
                                "description": "",
                            }
                            for i, f in enumerate(features)
                        ]

                # Create opportunity with AI analysis + Payment Intent data + Niche data
                opportunity = Opportunity(
                    raw_post_id=post.id,
                    title=analysis.get("title", content[:100]),
                    summary=analysis.get(
                        "summary", analysis.get("why_opportunity", "")
                    ),
                    product_type=analysis.get("product_type", "Other"),
                    sector=analysis.get("sector", "Other"),
                    business_model=analysis.get("business_model", "Subscription"),
                    demand_score=analysis.get("demand_score", 5),
                    market_score=analysis.get("market_score", 5),
                    feasibility_score=analysis.get("feasibility_score", 5),
                    revenue_score=analysis.get("revenue_score", 5),
                    total_score=analysis.get("total_score", 5),
                    confidence=analysis.get("confidence", 0.5),
                    competitors=competitors,
                    suggested_features=features,
                    go_to_market=analysis.get("go_to_market", ""),
                    # Payment Intent fields (Pivot 3)
                    payment_signal_tier=payment_result.tier,
                    payment_signal_strength=payment_result.strength,
                    mentioned_prices=[
                        {
                            "amount": p.amount,
                            "currency": p.currency,
                            "period": p.period,
                            "type": p.price_type,
                        }
                        for p in price_result.prices
                    ]
                    if price_result.prices
                    else None,
                    monthly_price_estimate=price_result.monthly_equivalent,
                    competitor_mentions=[
                        {
                            "name": m.name,
                            "category": m.category,
                            "sentiment": m.sentiment.value,
                            "churning": m.is_churning,
                        }
                        for m in competitor_result.mentions
                    ]
                    if competitor_result.mentions
                    else None,
                    churning_from=competitor_result.churning_from
                    if competitor_result.churning_from
                    else None,
                    purchase_journey_stage=journey_result.stage.value,
                    journey_confidence=journey_result.confidence,
                    revenue_potential_score=revenue_potential,
                    # Historical Success Validation fields (Pivot 4)
                    matched_patterns=[
                        {
                            "name": m.pattern.name,
                            "category": m.pattern.category.value,
                            "score": m.match_score,
                            "outcome": m.pattern.outcome_value,
                            "matched_signals": m.matched_signals,
                        }
                        for m in pattern_result.matches[:3]
                    ]
                    if pattern_result.matches
                    else None,
                    pattern_match_score=pattern_result.overall_score,
                    success_prediction=success_prediction.success_likelihood,
                    similar_successes=success_prediction.similar_successes
                    if success_prediction.similar_successes
                    else None,
                    success_factors=success_prediction.factors,
                    prediction_confidence=success_prediction.confidence,
                    risk_level=success_prediction.risk_level,
                    # Niche Focus fields (Pivot 2)
                    detected_niches=[
                        {
                            "niche_id": m.niche_id,
                            "niche_name": m.niche_name,
                            "confidence": m.confidence,
                            "matched_keywords": m.matched_keywords,
                        }
                        for m in niche_result.matches
                    ]
                    if niche_result.matches
                    else None,
                    primary_niche=primary_niche_id,
                    niche_fit_score=niche_fit_score,
                    niche_scores={
                        niche_id: {
                            "niche_name": score.niche_name,
                            "fit_score": score.niche_fit_score,
                            "opportunity_score": score.niche_opportunity_score,
                            "overall_score": score.overall_niche_score,
                            "market_attractiveness": score.market_attractiveness,
                            "competitive_landscape": score.competitive_landscape,
                            "recommendations": score.recommendations,
                        }
                        for niche_id, score in niche_scores_dict.items()
                    }
                    if niche_scores_dict
                    else None,
                )
                session.add(opportunity)
                opportunities_created += 1

                # Add to deduplication cache to prevent duplicates within this batch
                combined_text = f"{opportunity.title or ''} {opportunity.summary or ''}"
                deduplicator.add_to_cache(post.id, combined_text)

                logger.info(
                    f"Created opportunity: {opportunity.title[:50]}... "
                    f"(tier={payment_result.tier}, journey={journey_result.stage.value}, "
                    f"success={success_prediction.success_likelihood:.0f}%, "
                    f"niche={primary_niche_id or 'none'})"
                )

            except Exception as e:
                logger.error(f"Error processing post {post.id}: {e}")
                errors.append({"post_id": post.id, "error": str(e)})

        await session.commit()

    logger.info(
        f"Done! Created {opportunities_created}, skipped {skipped}, duplicates {duplicates}, errors {len(errors)}"
    )

    return {
        "opportunities_created": opportunities_created,
        "skipped": skipped,
        "duplicates_removed": duplicates,
        "errors": errors,
    }


def _calculate_revenue_potential(
    payment_result, price_result, competitor_result, journey_result
) -> float:
    """Calculate revenue potential score from payment intent signals.

    Scoring logic:
    - Payment signal tier contributes 0-40 points (tier 1=40, tier 4=10)
    - Journey stage contributes 0-30 points (churning/ready=30, aware=5)
    - Price mentions contribute 0-15 points (has price = 15)
    - Churning from competitors contributes 0-15 points (has churning = 15)

    Returns score from 0-10 (normalized from 0-100).
    """
    score = 0.0

    # Payment signal tier (40 points max)
    if payment_result.has_signal and payment_result.tier:
        tier_scores = {1: 40, 2: 30, 3: 25, 4: 10}
        score += tier_scores.get(payment_result.tier, 0)

    # Journey stage (30 points max)
    from app.analyzers.journey_classifier import JourneyStage

    journey_scores = {
        JourneyStage.CHURNING: 30,
        JourneyStage.READY: 30,
        JourneyStage.CONSIDERING: 20,
        JourneyStage.AWARE: 5,
        JourneyStage.UNAWARE: 0,
    }
    score += journey_scores.get(journey_result.stage, 0)

    # Price mentions (15 points max)
    if price_result.prices:
        score += 15

    # Churning from competitors (15 points max)
    if competitor_result.has_churning:
        score += 15

    # Normalize to 0-10 scale
    return round(score / 10, 1)


async def deep_analyze_opportunity(opportunity_id: int) -> dict:
    """Run deep AI analysis on a specific opportunity (for 'Start Working')."""
    ai_client = get_ai_client()

    async with get_db_context() as session:
        # Get opportunity with raw post
        query = select(Opportunity).where(Opportunity.id == opportunity_id)
        result = await session.execute(query)
        opportunity = result.scalar_one_or_none()

        if not opportunity:
            return {"error": "Opportunity not found"}

        # Get raw post content
        post_query = select(RawPost).where(RawPost.id == opportunity.raw_post_id)
        post_result = await session.execute(post_query)
        raw_post = post_result.scalar_one_or_none()

        content = raw_content if raw_post else opportunity.summary

        logger.info(f"Running deep analysis on: {opportunity.title[:50]}...")

        # Run deep analysis - all AI clients now support this via common interface
        analysis = await ai_client.deep_analysis(content, opportunity.title)

        # Update opportunity with deep analysis
        if "competitors" in analysis and analysis["competitors"]:
            opportunity.competitors = analysis["competitors"]

        if "suggested_features" in analysis and analysis["suggested_features"]:
            opportunity.suggested_features = analysis["suggested_features"]

        if "go_to_market" in analysis:
            gtm = analysis["go_to_market"]
            if isinstance(gtm, dict):
                opportunity.go_to_market = f"""Strategy: {gtm.get("strategy", "")}

Channels: {", ".join(gtm.get("channels", []))}

First Steps:
{chr(10).join("- " + s for s in gtm.get("first_steps", []))}"""
            else:
                opportunity.go_to_market = str(gtm)

        # Save notes with analysis details
        notes = []
        if "market_analysis" in analysis:
            ma = analysis["market_analysis"]
            notes.append(f"Target: {ma.get('target_audience', 'N/A')}")
            notes.append(f"Market Size: {ma.get('market_size', 'N/A')}")

        if "turkey_fit" in analysis:
            notes.append(f"Turkey Fit: {analysis['turkey_fit']}")

        if "risks" in analysis:
            notes.append(f"Risks: {', '.join(analysis.get('risks', []))}")

        if notes:
            opportunity.notes = "\n".join(notes)

        await session.commit()

        logger.info("Updated opportunity with deep insights")

        return {
            "success": True,
            "analysis": analysis,
        }


async def analyze_opportunity_sentiment(opportunity_id: int) -> dict:
    """Analyze sentiment from comments/content related to an opportunity."""
    ai_client = get_ai_client()

    async with get_db_context() as session:
        query = select(Opportunity).where(Opportunity.id == opportunity_id)
        result = await session.execute(query)
        opportunity = result.scalar_one_or_none()

        if not opportunity:
            return {"error": "Opportunity not found"}

        # Get raw post content
        post_query = select(RawPost).where(RawPost.id == opportunity.raw_post_id)
        post_result = await session.execute(post_query)
        raw_post = post_result.scalar_one_or_none()

        content = raw_content if raw_post else opportunity.summary

        logger.info(f"Analyzing sentiment for: {opportunity.title[:50]}...")

        sentiment = await ai_client.analyze_comment_sentiment(content)

        return {
            "opportunity_id": opportunity_id,
            "title": opportunity.title,
            "sentiment": sentiment,
        }


async def compare_opportunity_competitors(opportunity_id: int) -> dict:
    """Run competitor comparison analysis for an opportunity."""
    ai_client = get_ai_client()

    async with get_db_context() as session:
        query = select(Opportunity).where(Opportunity.id == opportunity_id)
        result = await session.execute(query)
        opportunity = result.scalar_one_or_none()

        if not opportunity:
            return {"error": "Opportunity not found"}

        # Get raw post content
        post_query = select(RawPost).where(RawPost.id == opportunity.raw_post_id)
        post_result = await session.execute(post_query)
        raw_post = post_result.scalar_one_or_none()

        content = raw_content if raw_post else opportunity.summary

        # Extract competitor names from stored data
        competitors = []
        if opportunity.competitors:
            for c in opportunity.competitors:
                if isinstance(c, dict):
                    competitors.append(c.get("name", ""))
                elif isinstance(c, str):
                    competitors.append(c)

        logger.info(f"Comparing competitors for: {opportunity.title[:50]}...")

        comparison = await ai_client.compare_competitors(content, competitors)

        return {
            "opportunity_id": opportunity_id,
            "title": opportunity.title,
            "competitor_comparison": comparison,
        }


async def define_opportunity_mvp(opportunity_id: int) -> dict:
    """Define MVP for an opportunity."""
    ai_client = get_ai_client()

    async with get_db_context() as session:
        query = select(Opportunity).where(Opportunity.id == opportunity_id)
        result = await session.execute(query)
        opportunity = result.scalar_one_or_none()

        if not opportunity:
            return {"error": "Opportunity not found"}

        # Build opportunity data dict
        opp_data = {
            "title": opportunity.title,
            "summary": opportunity.summary,
            "product_type": opportunity.product_type,
            "sector": opportunity.sector,
            "business_model": opportunity.business_model,
            "demand_score": opportunity.demand_score,
            "market_score": opportunity.market_score,
            "feasibility_score": opportunity.feasibility_score,
            "revenue_score": opportunity.revenue_score,
            "competitors": opportunity.competitors,
            "suggested_features": opportunity.suggested_features,
        }

        logger.info(f"Defining MVP for: {opportunity.title[:50]}...")

        mvp = await ai_client.define_mvp(opp_data)

        return {
            "opportunity_id": opportunity_id,
            "title": opportunity.title,
            "mvp": mvp,
        }


async def analyze_sector_trends(sector: str, limit: int = 20) -> dict:
    """Analyze trends for a specific sector based on recent opportunities."""
    ai_client = get_ai_client()

    async with get_db_context() as session:
        query = (
            select(Opportunity)
            .where(Opportunity.sector == sector)
            .order_by(Opportunity.created_at.desc())
            .limit(limit)
        )
        result = await session.execute(query)
        opportunities = result.scalars().all()

        if not opportunities:
            return {"error": f"No opportunities found for sector: {sector}"}

        # Build posts list for trend analysis
        posts = [
            {
                "title": opp.title,
                "content": opp.summary or "",
            }
            for opp in opportunities
        ]

        logger.info(f"Analyzing trends for sector: {sector} ({len(posts)} posts)")

        trends = await ai_client.analyze_trend(posts)

        return {
            "sector": sector,
            "posts_analyzed": len(posts),
            "trends": trends,
        }


async def calculate_opportunity_market_size(opportunity_id: int) -> dict:
    """Calculate TAM/SAM/SOM for an opportunity."""
    ai_client = get_ai_client()

    async with get_db_context() as session:
        query = select(Opportunity).where(Opportunity.id == opportunity_id)
        result = await session.execute(query)
        opportunity = result.scalar_one_or_none()

        if not opportunity:
            return {"error": "Opportunity not found"}

        # Build opportunity data dict
        opp_data = {
            "title": opportunity.title,
            "summary": opportunity.summary,
            "product_type": opportunity.product_type,
            "sector": opportunity.sector,
            "business_model": opportunity.business_model,
            "demand_score": opportunity.demand_score,
            "market_score": opportunity.market_score,
        }

        logger.info(f"Calculating market size for: {opportunity.title[:50]}...")

        market_size = await ai_client.calculate_market_size(opp_data)

        return {
            "opportunity_id": opportunity_id,
            "title": opportunity.title,
            "market_size": market_size,
        }


async def generate_opportunity_validation_plan(opportunity_id: int) -> dict:
    """Generate 48-hour validation plan for an opportunity."""
    ai_client = get_ai_client()

    async with get_db_context() as session:
        query = select(Opportunity).where(Opportunity.id == opportunity_id)
        result = await session.execute(query)
        opportunity = result.scalar_one_or_none()

        if not opportunity:
            return {"error": "Opportunity not found"}

        # Build opportunity data dict
        opp_data = {
            "title": opportunity.title,
            "summary": opportunity.summary,
            "product_type": opportunity.product_type,
            "sector": opportunity.sector,
            "business_model": opportunity.business_model,
            "demand_score": opportunity.demand_score,
            "market_score": opportunity.market_score,
            "feasibility_score": opportunity.feasibility_score,
            "revenue_score": opportunity.revenue_score,
            "competitors": opportunity.competitors,
            "suggested_features": opportunity.suggested_features,
        }

        logger.info(f"Generating validation plan for: {opportunity.title[:50]}...")

        validation_plan = await ai_client.generate_validation_plan(opp_data)

        return {
            "opportunity_id": opportunity_id,
            "title": opportunity.title,
            "validation_plan": validation_plan,
        }


async def analyze_opportunity_skills(opportunity_id: int) -> dict:
    """Analyze required skills and technologies to build an opportunity.

    Returns detailed skill requirements, recommended tech stack, solo-friendliness
    assessment, MVP complexity, no-code alternatives, and learning path.
    """
    ai_client = get_ai_client()

    async with get_db_context() as session:
        query = select(Opportunity).where(Opportunity.id == opportunity_id)
        result = await session.execute(query)
        opportunity = result.scalar_one_or_none()

        if not opportunity:
            return {"error": "Opportunity not found"}

        # Build opportunity data dict
        opp_data = {
            "title": opportunity.title,
            "summary": opportunity.summary,
            "product_type": opportunity.product_type,
            "sector": opportunity.sector,
            "business_model": opportunity.business_model,
            "demand_score": opportunity.demand_score,
            "market_score": opportunity.market_score,
            "feasibility_score": opportunity.feasibility_score,
            "revenue_score": opportunity.revenue_score,
            "competitors": opportunity.competitors,
            "suggested_features": opportunity.suggested_features,
        }

        logger.info(f"Analyzing skill requirements for: {opportunity.title[:50]}...")

        skill_analysis = await ai_client.analyze_skill_requirements(opp_data)

        return {
            "opportunity_id": opportunity_id,
            "title": opportunity.title,
            "skill_analysis": skill_analysis,
        }
