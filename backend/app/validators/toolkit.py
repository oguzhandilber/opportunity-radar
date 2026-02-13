"""Validation toolkit definitions.

Defines validation tool types and their characteristics for tracking
validation activities when testing opportunity hypotheses.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ValidationToolType(str, Enum):
    """Types of validation tools available."""
    LANDING_PAGE = "landing_page"
    EMAIL_LIST = "email_list"
    AD_CAMPAIGN = "ad_campaign"
    SURVEY = "survey"
    MVP = "mvp"
    SOCIAL_POST = "social_post"
    COLD_OUTREACH = "cold_outreach"
    WAITLIST = "waitlist"


@dataclass
class ValidationTool:
    """Definition of a validation tool."""
    tool_type: ValidationToolType
    name: str
    description: str
    setup_steps: list[str]
    expected_metrics: list[str]
    cost_estimate_min: float  # USD
    cost_estimate_max: float  # USD
    time_estimate_days: int
    difficulty: str  # "easy", "medium", "hard"
    best_for: list[str]  # What this tool is best for validating


class ValidationToolkit:
    """Catalog of validation tools and their characteristics."""

    @staticmethod
    def get_all_tools() -> list[ValidationTool]:
        """Get all available validation tools."""
        return [
            ValidationTool(
                tool_type=ValidationToolType.LANDING_PAGE,
                name="Landing Page Test",
                description="Create a simple landing page describing your product and measure interest",
                setup_steps=[
                    "Write compelling value proposition",
                    "Design simple landing page (use templates)",
                    "Add email signup form",
                    "Set up analytics tracking",
                    "Drive traffic via ads or social media"
                ],
                expected_metrics=[
                    "Page views",
                    "Email signups",
                    "Conversion rate (%)",
                    "Time on page",
                    "Bounce rate"
                ],
                cost_estimate_min=50,
                cost_estimate_max=500,
                time_estimate_days=3,
                difficulty="easy",
                best_for=[
                    "Testing product concept appeal",
                    "Measuring initial interest",
                    "Building email list",
                    "A/B testing messaging"
                ]
            ),
            ValidationTool(
                tool_type=ValidationToolType.EMAIL_LIST,
                name="Email List Building",
                description="Build an email list of interested potential customers",
                setup_steps=[
                    "Create lead magnet (guide, template, etc.)",
                    "Set up email capture form",
                    "Promote lead magnet to target audience",
                    "Send welcome sequence",
                    "Gauge interest with surveys"
                ],
                expected_metrics=[
                    "Email subscribers",
                    "Open rate (%)",
                    "Click-through rate (%)",
                    "Survey response rate",
                    "Purchase intent responses"
                ],
                cost_estimate_min=0,
                cost_estimate_max=200,
                time_estimate_days=7,
                difficulty="easy",
                best_for=[
                    "Building audience before launch",
                    "Validating pain points",
                    "Getting direct feedback",
                    "Pre-selling product"
                ]
            ),
            ValidationTool(
                tool_type=ValidationToolType.AD_CAMPAIGN,
                name="Paid Ad Campaign",
                description="Run targeted ads to test messaging and measure click-through rates",
                setup_steps=[
                    "Define target audience",
                    "Create ad variations (3-5)",
                    "Set up landing page",
                    "Configure ad platform (Google/Facebook/LinkedIn)",
                    "Run for 7-14 days",
                    "Analyze performance"
                ],
                expected_metrics=[
                    "Impressions",
                    "Click-through rate (CTR)",
                    "Cost per click (CPC)",
                    "Conversion rate",
                    "Cost per acquisition (CPA)"
                ],
                cost_estimate_min=100,
                cost_estimate_max=1000,
                time_estimate_days=7,
                difficulty="medium",
                best_for=[
                    "Testing market size",
                    "Validating messaging",
                    "Measuring acquisition cost",
                    "Fast market feedback"
                ]
            ),
            ValidationTool(
                tool_type=ValidationToolType.SURVEY,
                name="Customer Survey",
                description="Survey potential customers to understand needs and willingness to pay",
                setup_steps=[
                    "Define research questions",
                    "Create survey (10-15 questions max)",
                    "Find target respondents",
                    "Distribute survey",
                    "Analyze results"
                ],
                expected_metrics=[
                    "Survey responses",
                    "Completion rate",
                    "Pain point intensity (1-10)",
                    "Willingness to pay",
                    "Feature preferences"
                ],
                cost_estimate_min=0,
                cost_estimate_max=300,
                time_estimate_days=5,
                difficulty="easy",
                best_for=[
                    "Understanding pain points",
                    "Feature prioritization",
                    "Price sensitivity testing",
                    "Customer persona development"
                ]
            ),
            ValidationTool(
                tool_type=ValidationToolType.MVP,
                name="Minimum Viable Product",
                description="Build a simple working version with core features only",
                setup_steps=[
                    "Define absolute minimum feature set",
                    "Build basic prototype",
                    "Set up payment/signup flow",
                    "Recruit beta testers",
                    "Measure actual usage and retention"
                ],
                expected_metrics=[
                    "Active users",
                    "Retention rate (Day 1, 7, 30)",
                    "Feature usage",
                    "Conversion to paid",
                    "Customer feedback"
                ],
                cost_estimate_min=1000,
                cost_estimate_max=10000,
                time_estimate_days=30,
                difficulty="hard",
                best_for=[
                    "Validating actual usage",
                    "Testing core value proposition",
                    "Measuring retention",
                    "Getting real user feedback"
                ]
            ),
            ValidationTool(
                tool_type=ValidationToolType.SOCIAL_POST,
                name="Social Media Test",
                description="Post about the idea on social media and measure engagement",
                setup_steps=[
                    "Write compelling post about the problem/solution",
                    "Post to relevant communities",
                    "Engage with comments",
                    "Track engagement metrics",
                    "Follow up with interested users"
                ],
                expected_metrics=[
                    "Views/Impressions",
                    "Likes/Reactions",
                    "Comments",
                    "Shares",
                    "Direct messages/inquiries"
                ],
                cost_estimate_min=0,
                cost_estimate_max=50,
                time_estimate_days=1,
                difficulty="easy",
                best_for=[
                    "Quick market validation",
                    "Building initial buzz",
                    "Finding early adopters",
                    "Testing messaging"
                ]
            ),
            ValidationTool(
                tool_type=ValidationToolType.COLD_OUTREACH,
                name="Cold Outreach Campaign",
                description="Directly reach out to potential customers to gauge interest",
                setup_steps=[
                    "Identify target customer list (100-200 people)",
                    "Craft personalized outreach message",
                    "Send emails/LinkedIn messages",
                    "Track response rate",
                    "Schedule calls with interested parties"
                ],
                expected_metrics=[
                    "Messages sent",
                    "Response rate (%)",
                    "Positive responses",
                    "Calls booked",
                    "Expression of purchase intent"
                ],
                cost_estimate_min=0,
                cost_estimate_max=200,
                time_estimate_days=7,
                difficulty="medium",
                best_for=[
                    "B2B validation",
                    "Getting direct feedback",
                    "Building relationships",
                    "Understanding objections"
                ]
            ),
            ValidationTool(
                tool_type=ValidationToolType.WAITLIST,
                name="Pre-Launch Waitlist",
                description="Create waitlist to measure interest before building",
                setup_steps=[
                    "Create simple landing page",
                    "Add waitlist signup form",
                    "Optional: Add 'reserve spot' with deposit",
                    "Promote to target audience",
                    "Send updates to waitlist"
                ],
                expected_metrics=[
                    "Waitlist signups",
                    "Deposit/pre-orders (if applicable)",
                    "Email engagement",
                    "Referrals",
                    "Conversion rate"
                ],
                cost_estimate_min=0,
                cost_estimate_max=300,
                time_estimate_days=3,
                difficulty="easy",
                best_for=[
                    "Building anticipation",
                    "Measuring real commitment",
                    "Gathering early adopters",
                    "Validating pricing (with deposits)"
                ]
            )
        ]

    @staticmethod
    def get_tool(tool_type: ValidationToolType) -> Optional[ValidationTool]:
        """Get a specific validation tool by type."""
        tools = ValidationToolkit.get_all_tools()
        for tool in tools:
            if tool.tool_type == tool_type:
                return tool
        return None

    @staticmethod
    def get_tools_by_difficulty(difficulty: str) -> list[ValidationTool]:
        """Get tools filtered by difficulty level."""
        return [
            tool for tool in ValidationToolkit.get_all_tools()
            if tool.difficulty == difficulty
        ]

    @staticmethod
    def get_tools_by_budget(max_budget: float) -> list[ValidationTool]:
        """Get tools within a budget constraint."""
        return [
            tool for tool in ValidationToolkit.get_all_tools()
            if tool.cost_estimate_min <= max_budget
        ]

    @staticmethod
    def get_tools_by_timeframe(max_days: int) -> list[ValidationTool]:
        """Get tools that can be completed within timeframe."""
        return [
            tool for tool in ValidationToolkit.get_all_tools()
            if tool.time_estimate_days <= max_days
        ]
