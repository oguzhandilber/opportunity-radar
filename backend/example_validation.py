"""Example usage of the Validation system."""

import asyncio
from app.database import init_db, get_db_context, Opportunity, RawPost, ValidationExperiment
from app.validators.landing_generator import LandingPageGenerator
from app.validators.validation_scorer import ValidationScorer


async def example_usage():
    """Demonstrate the validation system."""

    # Initialize database
    await init_db()

    async with get_db_context() as session:
        # Create a sample opportunity
        post = RawPost(
            source="reddit",
            external_id="example123",
            content="I need a tool to manage my freelance projects better",
        )
        session.add(post)
        await session.flush()

        opportunity = Opportunity(
            raw_post_id=post.id,
            title="Freelance Project Management SaaS",
            summary="A comprehensive project management tool designed for freelancers and small agencies to track time, manage clients, and generate invoices.",
            product_type="SaaS",
            sector="Productivity",
            suggested_features=[
                {"feature": "Time tracking", "priority": "high"},
                {"feature": "Invoice generation", "priority": "high"},
                {"feature": "Client portal", "priority": "medium"},
                {"feature": "Project templates", "priority": "low"},
            ],
            competitors=[
                {"name": "Toggl", "url": "https://toggl.com"},
                {"name": "Harvest", "url": "https://harvestapp.com"},
            ],
            status="new",
        )
        session.add(opportunity)
        await session.flush()

        print("=" * 80)
        print("VALIDATION EXAMPLE")
        print("=" * 80)

        # 1. Calculate validation score
        print("\n1. VALIDATION SCORE")
        print("-" * 80)
        score = ValidationScorer.score_opportunity(
            title=opportunity.title,
            summary=opportunity.summary,
            product_type=opportunity.product_type,
            sector=opportunity.sector,
            suggested_features=opportunity.suggested_features,
            competitors=opportunity.competitors,
        )

        print(f"Total Score: {score['total_score']}/10")
        print(f"  - Specificity: {score['specificity']}/10")
        print(f"  - Actionability: {score['actionability']}/10")
        print(f"  - Testability: {score['testability']}/10")
        print("\nRecommended Experiments:")
        for exp in score['recommended_experiments']:
            print(f"  [{exp['priority'].upper()}] {exp['type']}: {exp['reason']}")

        # 2. Generate landing page
        print("\n2. LANDING PAGE GENERATION")
        print("-" * 80)

        features = [f["feature"] for f in opportunity.suggested_features[:3]]

        html = LandingPageGenerator.generate_problem_solution(
            title=opportunity.title,
            problem="Managing freelance projects, tracking time, and creating invoices is time-consuming and chaotic across multiple tools.",
            solution="An all-in-one platform that handles project management, time tracking, and invoicing for freelancers.",
            features=features,
            cta_text="Join the Waitlist",
        )

        print(f"Generated HTML length: {len(html)} characters")
        print(f"First 200 chars: {html[:200]}...")

        # Save to file
        output_file = "/tmp/validation_landing_page.html"
        with open(output_file, "w") as f:
            f.write(html)
        print(f"\nLanding page saved to: {output_file}")
        print("You can open this file in a browser to see the result!")

        # 3. Create validation experiment
        print("\n3. CREATE EXPERIMENT")
        print("-" * 80)

        experiment = ValidationExperiment(
            opportunity_id=opportunity.id,
            experiment_type="landing_page",
            hypothesis="At least 100 freelancers will sign up within 2 weeks",
            target_metric="email_signups",
            status="draft",
            landing_page_html=html,
        )
        session.add(experiment)
        await session.flush()

        print(f"Experiment ID: {experiment.id}")
        print(f"Type: {experiment.experiment_type}")
        print(f"Hypothesis: {experiment.hypothesis}")
        print(f"Target Metric: {experiment.target_metric}")
        print(f"Status: {experiment.status}")

        # 4. Simulate recording results
        print("\n4. RECORD RESULTS (SIMULATED)")
        print("-" * 80)

        experiment.results = {
            "signups": 127,
            "page_views": 850,
            "conversion_rate": 0.149,
            "sources": {
                "reddit": 45,
                "twitter": 32,
                "product_hunt": 50,
            }
        }
        experiment.status = "completed"
        await session.flush()

        print("Results recorded:")
        print(f"  - Signups: {experiment.results['signups']}")
        print(f"  - Page Views: {experiment.results['page_views']}")
        print(f"  - Conversion Rate: {experiment.results['conversion_rate']:.1%}")
        print(f"  - Status: {experiment.status}")

        print("\n" + "=" * 80)
        print("VALIDATION COMPLETE!")
        print("=" * 80)
        print("\nNext steps:")
        print("1. Deploy the landing page to Netlify/Vercel/GitHub Pages")
        print("2. Share on Reddit, Twitter, Product Hunt")
        print("3. Track signups and engagement")
        print("4. Decide whether to build based on validation results")
        print("\nGoal achieved: 127 signups > 100 target ✅")


if __name__ == "__main__":
    asyncio.run(example_usage())
