"""Validation playbooks API - step-by-step validation guides."""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_session, Opportunity, ValidationExperiment
from app.api.auth import get_current_user

router = APIRouter()


# Pydantic schemas
class ValidationStep(BaseModel):
    step_number: int
    title: str
    description: str
    action_items: List[str]
    expected_outcome: str
    success_criteria: str
    tools_needed: List[str]
    estimated_time: str
    cost_estimate: Optional[str] = None


class ValidationPlaybook(BaseModel):
    id: str
    name: str
    description: str
    experiment_type: str
    difficulty: str  # easy, medium, hard
    estimated_total_time: str
    estimated_cost: str
    steps: List[ValidationStep]
    best_for: List[str]
    metrics_to_track: List[str]
    success_indicators: List[str]


class ValidationPlaybookRequest(BaseModel):
    opportunity_id: int
    playbook_id: str


class ValidationPlaybookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    opportunity_id: int
    opportunity_title: str
    playbook: ValidationPlaybook
    customized_steps: Optional[List[ValidationStep]] = None
    recommendations: Optional[List[str]] = None


# Validation playbook definitions
VALIDATION_PLAYBOOKS = {
    "landing_page_test": ValidationPlaybook(
        id="landing_page_test",
        name="Landing Page Validation Test",
        description="Create a simple landing page to validate product concept and measure interest through email signups.",
        experiment_type="landing_page",
        difficulty="easy",
        estimated_total_time="3-5 days",
        estimated_cost="$50-200",
        best_for=[
            "Testing product concept appeal",
            "Measuring initial interest",
            "Building email list",
            "A/B testing messaging",
        ],
        metrics_to_track=[
            "Page views",
            "Email signups",
            "Conversion rate (%)",
            "Time on page",
            "Bounce rate",
        ],
        success_indicators=[
            ">5% email conversion rate",
            ">100 page views in first week",
            "Low bounce rate (<60%)",
            "Multiple signups from target segment",
        ],
        steps=[
            ValidationStep(
                step_number=1,
                title="Define Your Value Proposition",
                description="Clearly articulate the problem you're solving and your unique solution.",
                action_items=[
                    "Write a compelling headline (10 words or less)",
                    "Define 3 key benefits (not features)",
                    "Identify your target audience",
                    "Create a simple tagline",
                ],
                expected_outcome="Clear, concise value proposition statement",
                success_criteria="Can explain your value prop in 30 seconds",
                tools_needed=["Google Docs", "Notion"],
                estimated_time="2-4 hours",
                cost_estimate="Free",
            ),
            ValidationStep(
                step_number=2,
                title="Design Your Landing Page",
                description="Create a simple, focused landing page using templates or no-code tools.",
                action_items=[
                    "Choose a template (Carrd, Webflow, or Unbounce)",
                    "Write compelling copy",
                    "Add email capture form",
                    "Include clear call-to-action",
                    "Set up basic analytics (Google Analytics)",
                ],
                expected_outcome="Live landing page with email capture",
                success_criteria="Page loads fast, mobile-friendly, clear CTA",
                tools_needed=["Carrd", "Webflow", "Unbounce", "Google Analytics"],
                estimated_time="1 day",
                cost_estimate="$19-50",
            ),
            ValidationStep(
                step_number=3,
                title="Drive Targeted Traffic",
                description="Get your page in front of potential customers through various channels.",
                action_items=[
                    "Post on relevant Reddit communities",
                    "Share in targeted Facebook/LinkedIn groups",
                    "Run small ad campaign ($50-100)",
                    "Reach out to potential users directly",
                    "Post on Product Hunt (if ready)",
                ],
                expected_outcome="100+ targeted visitors to your page",
                success_criteria="Diverse traffic sources, engaged visitors",
                tools_needed=["Google Ads", "Facebook Ads", "Reddit"],
                estimated_time="2-3 days",
                cost_estimate="$50-100",
            ),
            ValidationStep(
                step_number=4,
                title="Analyze Results & Decide",
                description="Review metrics and determine if there's enough interest to proceed.",
                action_items=[
                    "Calculate conversion rate",
                    "Analyze traffic sources",
                    "Review email signup quality",
                    "Survey interested users",
                    "Make go/no-go decision",
                ],
                expected_outcome="Clear validation decision with data",
                success_criteria=">5% conversion rate OR 50+ quality signups",
                tools_needed=["Google Analytics", "Typeform"],
                estimated_time="1 day",
                cost_estimate="Free",
            ),
        ],
    ),
    "waitlist_validation": ValidationPlaybook(
        id="waitlist_validation",
        name="Pre-Launch Waitlist",
        description="Build a waitlist to measure real commitment before building your product.",
        experiment_type="waitlist",
        difficulty="easy",
        estimated_total_time="1-2 weeks",
        estimated_cost="$0-100",
        best_for=[
            "Building anticipation",
            "Measuring real commitment",
            "Gathering early adopters",
            "Validating pricing",
        ],
        metrics_to_track=[
            "Waitlist signups",
            "Referral rate",
            "Email engagement",
            "Pre-order conversions (if applicable)",
        ],
        success_indicators=[
            "100+ waitlist signups in 2 weeks",
            ">30% open rate on emails",
            "Active referrals from existing signups",
            "Multiple pricing inquiries",
        ],
        steps=[
            ValidationStep(
                step_number=1,
                title="Create Waitlist Landing Page",
                description="Build a compelling waitlist page with value proposition and signup form.",
                action_items=[
                    "Design waitlist page with clear benefits",
                    "Add social proof elements",
                    "Include referral mechanism",
                    "Set up email sequence",
                    "Add urgency/scarcity (optional)",
                ],
                expected_outcome="Professional waitlist page ready",
                success_criteria="Clear value prop, easy signup, mobile-optimized",
                tools_needed=["Carrd", "Mailchimp", "ConvertKit"],
                estimated_time="1-2 days",
                cost_estimate="$0-29",
            ),
            ValidationStep(
                step_number=2,
                title="Launch & Promote",
                description="Get the word out through your network and relevant communities.",
                action_items=[
                    "Share with personal network",
                    "Post on social media",
                    "Submit to BetaList",
                    "Share in relevant communities",
                    "Reach out to potential users directly",
                ],
                expected_outcome="Initial wave of signups",
                success_criteria="20+ signups in first 48 hours",
                tools_needed=["Twitter", "LinkedIn", "BetaList"],
                estimated_time="3-5 days",
                cost_estimate="Free",
            ),
            ValidationStep(
                step_number=3,
                title="Nurture & Engage",
                description="Keep waitlist members engaged with updates and valuable content.",
                action_items=[
                    "Send welcome email sequence",
                    "Share behind-the-scenes content",
                    "Ask for feedback/survey",
                    "Provide early access teasers",
                    "Build community (Discord/Slack)",
                ],
                expected_outcome="Engaged waitlist community",
                success_criteria=">30% email open rate, active responses",
                tools_needed=["ConvertKit", "Typeform", "Discord"],
                estimated_time="Ongoing (1-2 hrs/week)",
                cost_estimate="Free",
            ),
        ],
    ),
    "mvp_prototype": ValidationPlaybook(
        id="mvp_prototype",
        name="MVP Prototype Test",
        description="Build a minimal prototype to test core functionality with real users.",
        experiment_type="mvp",
        difficulty="hard",
        estimated_total_time="2-4 weeks",
        estimated_cost="$500-2000",
        best_for=[
            "Validating core value proposition",
            "Testing user workflows",
            "Getting real usage data",
            "Refining product-market fit",
        ],
        metrics_to_track=[
            "User activation rate",
            "Feature usage",
            "Retention (Day 1, 7, 30)",
            "User feedback scores",
            "Support requests",
        ],
        success_indicators=[
            ">40% user activation",
            ">20% Day 7 retention",
            "Positive NPS score (>30)",
            "Core feature adoption >60%",
        ],
        steps=[
            ValidationStep(
                step_number=1,
                title="Define MVP Scope",
                description="Identify the absolute minimum features needed to deliver core value.",
                action_items=[
                    "Map user journey",
                    "Identify 'must-have' vs 'nice-to-have' features",
                    "Define success metrics",
                    "Create user stories",
                    "Set timeline constraints",
                ],
                expected_outcome="Clear MVP feature list",
                success_criteria="Can deliver value in <3 features",
                tools_needed=["Notion", "Miro", "Figma"],
                estimated_time="2-3 days",
                cost_estimate="Free",
            ),
            ValidationStep(
                step_number=2,
                title="Build Prototype",
                description="Create a working prototype using no-code or rapid development.",
                action_items=[
                    "Choose tech stack (no-code or code)",
                    "Build core user flows",
                    "Implement key features",
                    "Add basic analytics",
                    "Set up user feedback mechanism",
                ],
                expected_outcome="Working prototype ready for testing",
                success_criteria="Core workflow functional, can onboard users",
                tools_needed=["Bubble", "Webflow", "Retool", "Firebase"],
                estimated_time="1-3 weeks",
                cost_estimate="$100-500",
            ),
            ValidationStep(
                step_number=3,
                title="Recruit Beta Users",
                description="Find 10-20 ideal users to test your prototype.",
                action_items=[
                    "Define ideal tester profile",
                    "Reach out to potential users",
                    "Screen and select participants",
                    "Set up onboarding process",
                    "Establish communication channel",
                ],
                expected_outcome="10-20 committed beta testers",
                success_criteria="Diverse user base, high engagement potential",
                tools_needed=["Typeform", "Calendly", "Slack"],
                estimated_time="3-5 days",
                cost_estimate="Free",
            ),
            ValidationStep(
                step_number=4,
                title="Run Beta Test",
                description="Launch with beta users and closely monitor usage and feedback.",
                action_items=[
                    "Onboard beta users",
                    "Monitor usage analytics",
                    "Collect feedback (survey/interviews)",
                    "Track support requests",
                    "Iterate based on feedback",
                ],
                expected_outcome="Validated (or invalidated) core assumptions",
                success_criteria=">40% activation, positive feedback, usage data",
                tools_needed=["Mixpanel", "Amplitude", "Typeform"],
                estimated_time="1-2 weeks",
                cost_estimate="$50-100",
            ),
        ],
    ),
    "cold_outreach": ValidationPlaybook(
        id="cold_outreach",
        name="Cold Outreach Campaign",
        description="Direct outreach to potential customers to validate demand and gather feedback.",
        experiment_type="cold_outreach",
        difficulty="medium",
        estimated_total_time="1-2 weeks",
        estimated_cost="$0-200",
        best_for=[
            "B2B validation",
            "Getting direct feedback",
            "Building relationships",
            "Understanding objections",
        ],
        metrics_to_track=[
            "Messages sent",
            "Response rate (%)",
            "Positive responses",
            "Calls booked",
            "Purchase intent expressed",
        ],
        success_indicators=[
            ">10% response rate",
            "Multiple positive responses",
            "3+ calls booked",
            "Clear demand signals",
        ],
        steps=[
            ValidationStep(
                step_number=1,
                title="Build Target List",
                description="Identify and research 100-200 ideal potential customers.",
                action_items=[
                    "Define ideal customer profile",
                    "Find contacts on LinkedIn",
                    "Research companies/roles",
                    "Verify email addresses",
                    "Organize in spreadsheet/CRM",
                ],
                expected_outcome="Qualified list of 100+ prospects",
                success_criteria="Clear fit with target profile, verified contacts",
                tools_needed=["LinkedIn", "Hunter.io", "Apollo.io"],
                estimated_time="2-3 days",
                cost_estimate="$0-50",
            ),
            ValidationStep(
                step_number=2,
                title="Craft Outreach Message",
                description="Write personalized, compelling outreach messages.",
                action_items=[
                    "Write 3 message templates",
                    "Personalize first line",
                    "Include clear value proposition",
                    "Add soft call-to-action",
                    "Create follow-up sequence",
                ],
                expected_outcome="Ready-to-send message templates",
                success_criteria="<100 words, personalized, clear value",
                tools_needed=["Google Docs", "Lavender"],
                estimated_time="4-6 hours",
                cost_estimate="Free",
            ),
            ValidationStep(
                step_number=3,
                title="Execute Campaign",
                description="Send personalized messages and manage responses.",
                action_items=[
                    "Send 20-30 messages/day",
                    "Track opens/clicks/replies",
                    "Respond to interested prospects",
                    "Book discovery calls",
                    "Log feedback and objections",
                ],
                expected_outcome="Meaningful conversations with prospects",
                success_criteria="Responses and calls booked",
                tools_needed=["Gmail", "Mixmax", "Outreach"],
                estimated_time="1 week",
                cost_estimate="Free",
            ),
            ValidationStep(
                step_number=4,
                title="Analyze & Iterate",
                description="Review results and refine your approach.",
                action_items=[
                    "Calculate response rates",
                    "Identify common objections",
                    "Analyze successful messages",
                    "Update messaging based on learnings",
                    "Decide on next steps",
                ],
                expected_outcome="Clear validation signals and refined approach",
                success_criteria=">10% response, clear demand or pivot needed",
                tools_needed=["Spreadsheet", "CRM"],
                estimated_time="1 day",
                cost_estimate="Free",
            ),
        ],
    ),
}


@router.get("/playbooks", response_model=List[ValidationPlaybook])
async def list_playbooks(current_user: dict = Depends(get_current_user)):
    """List all available validation playbooks."""
    return list(VALIDATION_PLAYBOOKS.values())


@router.get("/playbooks/{playbook_id}", response_model=ValidationPlaybook)
async def get_playbook(
    playbook_id: str, current_user: dict = Depends(get_current_user)
):
    """Get a specific validation playbook."""
    if playbook_id not in VALIDATION_PLAYBOOKS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Playbook not found"
        )

    return VALIDATION_PLAYBOOKS[playbook_id]


@router.post(
    "/opportunities/{opportunity_id}/playbook",
    response_model=ValidationPlaybookResponse,
)
async def assign_playbook_to_opportunity(
    opportunity_id: int,
    request: ValidationPlaybookRequest,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Assign a validation playbook to an opportunity with customization."""

    # Check if opportunity exists
    stmt = select(Opportunity).where(Opportunity.id == opportunity_id)
    result = await session.execute(stmt)
    opportunity = result.scalar_one_or_none()

    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found"
        )

    # Check if playbook exists
    if request.playbook_id not in VALIDATION_PLAYBOOKS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Playbook not found"
        )

    playbook = VALIDATION_PLAYBOOKS[request.playbook_id]

    # Customize steps based on opportunity
    customized_steps = []
    recommendations = []

    for step in playbook.steps:
        customized_step = step.copy()

        # Add opportunity-specific context to action items
        if opportunity.sector:
            customized_step.action_items.append(
                f"Tailor messaging for {opportunity.sector} sector"
            )

        if opportunity.target_audience:
            customized_step.action_items.append(
                f"Focus on {opportunity.target_audience} audience"
            )

        customized_steps.append(customized_step)

    # Generate recommendations based on opportunity data
    if opportunity.total_score and opportunity.total_score >= 8:
        recommendations.append("High-scoring opportunity - prioritize rapid validation")

    if opportunity.competitors and len(opportunity.competitors) > 5:
        recommendations.append(
            "Competitive market - focus on differentiation in validation"
        )

    if opportunity.revenue_potential_score and opportunity.revenue_potential_score >= 8:
        recommendations.append(
            "High revenue potential - consider pricing validation tests"
        )

    recommendations.append(
        f"Use {playbook.name} approach for best results with this opportunity type"
    )

    return ValidationPlaybookResponse(
        opportunity_id=opportunity_id,
        opportunity_title=opportunity.title,
        playbook=playbook,
        customized_steps=customized_steps,
        recommendations=recommendations,
    )


@router.get("/opportunities/{opportunity_id}/recommend-playbook")
async def recommend_playbook(
    opportunity_id: int,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get playbook recommendations based on opportunity characteristics."""

    stmt = select(Opportunity).where(Opportunity.id == opportunity_id)
    result = await session.execute(stmt)
    opportunity = result.scalar_one_or_none()

    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found"
        )

    # Score each playbook based on opportunity fit
    scored_playbooks = []

    for playbook in VALIDATION_PLAYBOOKS.values():
        score = 0
        reasons = []

        # Score based on opportunity characteristics
        if opportunity.business_model == "B2B" and playbook.id == "cold_outreach":
            score += 30
            reasons.append("B2B opportunity - cold outreach highly effective")

        if opportunity.total_score and opportunity.total_score >= 7.5:
            score += 20
            reasons.append("High score indicates strong validation potential")

        if opportunity.feasibility_score and opportunity.feasibility_score >= 7:
            if playbook.id == "mvp_prototype":
                score += 25
                reasons.append("High feasibility - MVP approach recommended")

        if opportunity.product_type == "SaaS" and playbook.id == "landing_page_test":
            score += 20
            reasons.append("SaaS products validate well with landing pages")

        if (
            opportunity.revenue_potential_score
            and opportunity.revenue_potential_score >= 8
        ):
            if playbook.id == "waitlist_validation":
                score += 15
                reasons.append("High revenue potential - build waitlist for launch")

        scored_playbooks.append(
            {"playbook": playbook, "score": score, "reasons": reasons}
        )

    # Sort by score
    scored_playbooks.sort(key=lambda x: x["score"], reverse=True)

    return {
        "opportunity_id": opportunity_id,
        "opportunity_title": opportunity.title,
        "recommendations": [
            {
                "playbook_id": rec["playbook"].id,
                "playbook_name": rec["playbook"].name,
                "match_score": rec["score"],
                "confidence": "high"
                if rec["score"] > 50
                else "medium"
                if rec["score"] > 30
                else "low",
                "reasoning": rec["reasons"],
            }
            for rec in scored_playbooks[:3]
        ],
        "suggested_approach": f"Start with {scored_playbooks[0]['playbook'].name} based on your opportunity profile",
    }
