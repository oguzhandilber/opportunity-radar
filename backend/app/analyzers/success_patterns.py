"""Success pattern database for historical validation.

Contains curated examples of successful startups/products with their
original pain points, solution patterns, and outcomes.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class OutcomeType(Enum):
    """Type of successful outcome."""
    IPO = "ipo"
    ACQUISITION = "acquisition"
    UNICORN = "unicorn"  # $1B+ valuation
    PROFITABLE = "profitable"
    HIGH_GROWTH = "high_growth"


class Category(Enum):
    """Product category."""
    COMMUNICATION = "communication"
    PRODUCTIVITY = "productivity"
    DEVELOPER_TOOLS = "developer_tools"
    DESIGN = "design"
    MARKETING = "marketing"
    SALES = "sales"
    HR = "hr"
    FINANCE = "finance"
    EDUCATION = "education"
    ECOMMERCE = "ecommerce"
    ANALYTICS = "analytics"
    SECURITY = "security"
    AI_ML = "ai_ml"
    NO_CODE = "no_code"
    VIDEO = "video"
    SOCIAL = "social"
    HEALTH = "health"
    INFRASTRUCTURE = "infrastructure"


@dataclass
class SuccessPattern:
    """A successful product/startup pattern."""
    name: str
    category: Category
    original_pain: str  # The pain point they solved
    solution_type: str  # Type of solution (SaaS, marketplace, etc.)
    outcome: OutcomeType
    outcome_value: str  # e.g., "$27B", "$3B"
    year_founded: int
    signals: list[str]  # Keywords/signals that would have predicted this
    target_audience: str
    key_differentiator: str


class SuccessPatternDatabase:
    """Database of successful startup patterns."""

    PATTERNS: list[SuccessPattern] = [
        # Communication
        SuccessPattern(
            name="Slack",
            category=Category.COMMUNICATION,
            original_pain="Email overload for team communication",
            solution_type="Team messaging platform",
            outcome=OutcomeType.ACQUISITION,
            outcome_value="$27B",
            year_founded=2013,
            signals=["email", "team", "chat", "communication", "messaging", "workplace"],
            target_audience="Teams and businesses",
            key_differentiator="Channels and integrations",
        ),
        SuccessPattern(
            name="Discord",
            category=Category.COMMUNICATION,
            original_pain="Voice chat for gamers was fragmented",
            solution_type="Voice/text chat platform",
            outcome=OutcomeType.UNICORN,
            outcome_value="$15B",
            year_founded=2015,
            signals=["gaming", "voice", "chat", "community", "server", "friends"],
            target_audience="Gamers and communities",
            key_differentiator="Low latency voice + community features",
        ),
        SuccessPattern(
            name="Zoom",
            category=Category.COMMUNICATION,
            original_pain="Video conferencing was unreliable and complex",
            solution_type="Video conferencing",
            outcome=OutcomeType.IPO,
            outcome_value="$100B+ peak",
            year_founded=2011,
            signals=["video", "meeting", "conference", "remote", "call", "webinar"],
            target_audience="Businesses and individuals",
            key_differentiator="Reliability and ease of use",
        ),
        SuccessPattern(
            name="Loom",
            category=Category.VIDEO,
            original_pain="Async video communication was hard",
            solution_type="Async video messaging",
            outcome=OutcomeType.ACQUISITION,
            outcome_value="$1.5B",
            year_founded=2015,
            signals=["video", "async", "screen recording", "explain", "tutorial", "demo"],
            target_audience="Remote teams",
            key_differentiator="Quick recording and sharing",
        ),
        SuccessPattern(
            name="Intercom",
            category=Category.COMMUNICATION,
            original_pain="Customer communication was fragmented",
            solution_type="Customer messaging platform",
            outcome=OutcomeType.UNICORN,
            outcome_value="$1.3B",
            year_founded=2011,
            signals=["customer", "support", "chat", "messaging", "help", "widget"],
            target_audience="SaaS businesses",
            key_differentiator="In-app messaging + automation",
        ),

        # Productivity
        SuccessPattern(
            name="Notion",
            category=Category.PRODUCTIVITY,
            original_pain="Notes, docs, and wikis were separate tools",
            solution_type="All-in-one workspace",
            outcome=OutcomeType.UNICORN,
            outcome_value="$10B",
            year_founded=2016,
            signals=["notes", "wiki", "docs", "workspace", "organize", "team knowledge"],
            target_audience="Teams and individuals",
            key_differentiator="Flexible blocks + databases",
        ),
        SuccessPattern(
            name="Airtable",
            category=Category.PRODUCTIVITY,
            original_pain="Spreadsheets weren't flexible enough for databases",
            solution_type="Spreadsheet-database hybrid",
            outcome=OutcomeType.UNICORN,
            outcome_value="$11B",
            year_founded=2012,
            signals=["spreadsheet", "database", "organize", "track", "table", "workflow"],
            target_audience="Teams needing custom databases",
            key_differentiator="Spreadsheet UI with database power",
        ),
        SuccessPattern(
            name="Calendly",
            category=Category.PRODUCTIVITY,
            original_pain="Scheduling meetings was email ping-pong",
            solution_type="Scheduling automation",
            outcome=OutcomeType.UNICORN,
            outcome_value="$3B",
            year_founded=2013,
            signals=["schedule", "meeting", "calendar", "book", "appointment", "availability"],
            target_audience="Professionals",
            key_differentiator="Simple link-based scheduling",
        ),
        SuccessPattern(
            name="Asana",
            category=Category.PRODUCTIVITY,
            original_pain="Project management was too complex",
            solution_type="Work management platform",
            outcome=OutcomeType.IPO,
            outcome_value="$5B+ peak",
            year_founded=2008,
            signals=["project", "task", "team", "work", "manage", "track", "deadline"],
            target_audience="Teams",
            key_differentiator="Task-centric workflow",
        ),
        SuccessPattern(
            name="Monday.com",
            category=Category.PRODUCTIVITY,
            original_pain="Work OS for teams was missing",
            solution_type="Work operating system",
            outcome=OutcomeType.IPO,
            outcome_value="$7B+ peak",
            year_founded=2012,
            signals=["workflow", "project", "team", "board", "manage", "automate"],
            target_audience="Teams",
            key_differentiator="Visual work management",
        ),
        SuccessPattern(
            name="Trello",
            category=Category.PRODUCTIVITY,
            original_pain="Simple task boards were missing",
            solution_type="Kanban boards",
            outcome=OutcomeType.ACQUISITION,
            outcome_value="$425M",
            year_founded=2011,
            signals=["board", "card", "kanban", "organize", "drag", "simple"],
            target_audience="Teams and individuals",
            key_differentiator="Visual simplicity",
        ),
        SuccessPattern(
            name="Todoist",
            category=Category.PRODUCTIVITY,
            original_pain="Personal task management was clunky",
            solution_type="Task manager",
            outcome=OutcomeType.PROFITABLE,
            outcome_value="$100M+ ARR",
            year_founded=2007,
            signals=["todo", "task", "list", "organize", "productivity", "remember"],
            target_audience="Individuals",
            key_differentiator="Natural language input",
        ),

        # Developer Tools
        SuccessPattern(
            name="GitHub",
            category=Category.DEVELOPER_TOOLS,
            original_pain="Code collaboration was hard",
            solution_type="Code hosting platform",
            outcome=OutcomeType.ACQUISITION,
            outcome_value="$7.5B",
            year_founded=2008,
            signals=["code", "git", "repository", "developer", "open source", "collaborate"],
            target_audience="Developers",
            key_differentiator="Social coding",
        ),
        SuccessPattern(
            name="GitLab",
            category=Category.DEVELOPER_TOOLS,
            original_pain="DevOps was fragmented across tools",
            solution_type="DevOps platform",
            outcome=OutcomeType.IPO,
            outcome_value="$11B peak",
            year_founded=2014,
            signals=["devops", "ci/cd", "git", "pipeline", "deploy", "code"],
            target_audience="Development teams",
            key_differentiator="All-in-one DevOps",
        ),
        SuccessPattern(
            name="Vercel",
            category=Category.DEVELOPER_TOOLS,
            original_pain="Deploying frontend was complex",
            solution_type="Frontend deployment platform",
            outcome=OutcomeType.UNICORN,
            outcome_value="$2.5B",
            year_founded=2015,
            signals=["deploy", "frontend", "hosting", "serverless", "next.js", "edge"],
            target_audience="Frontend developers",
            key_differentiator="Zero-config deployment",
        ),
        SuccessPattern(
            name="Stripe",
            category=Category.DEVELOPER_TOOLS,
            original_pain="Payment integration was painful",
            solution_type="Payment API",
            outcome=OutcomeType.UNICORN,
            outcome_value="$95B peak",
            year_founded=2010,
            signals=["payment", "api", "developer", "billing", "subscription", "checkout"],
            target_audience="Developers",
            key_differentiator="Developer-first API",
        ),
        SuccessPattern(
            name="Twilio",
            category=Category.DEVELOPER_TOOLS,
            original_pain="Communication APIs were hard to build",
            solution_type="Communication API",
            outcome=OutcomeType.IPO,
            outcome_value="$60B peak",
            year_founded=2008,
            signals=["sms", "voice", "api", "communication", "messaging", "developer"],
            target_audience="Developers",
            key_differentiator="Simple communication APIs",
        ),
        SuccessPattern(
            name="Postman",
            category=Category.DEVELOPER_TOOLS,
            original_pain="API testing was manual and tedious",
            solution_type="API development platform",
            outcome=OutcomeType.UNICORN,
            outcome_value="$5.6B",
            year_founded=2014,
            signals=["api", "test", "developer", "request", "collection", "documentation"],
            target_audience="Developers",
            key_differentiator="API collaboration",
        ),

        # Design
        SuccessPattern(
            name="Figma",
            category=Category.DESIGN,
            original_pain="Design collaboration required files",
            solution_type="Collaborative design tool",
            outcome=OutcomeType.ACQUISITION,
            outcome_value="$20B",
            year_founded=2012,
            signals=["design", "collaborate", "prototype", "ui", "ux", "figma"],
            target_audience="Designers and teams",
            key_differentiator="Browser-based real-time collaboration",
        ),
        SuccessPattern(
            name="Canva",
            category=Category.DESIGN,
            original_pain="Design tools were too complex for non-designers",
            solution_type="Simple design tool",
            outcome=OutcomeType.UNICORN,
            outcome_value="$40B",
            year_founded=2012,
            signals=["design", "template", "easy", "graphics", "social media", "poster"],
            target_audience="Non-designers",
            key_differentiator="Templates and simplicity",
        ),
        SuccessPattern(
            name="Miro",
            category=Category.DESIGN,
            original_pain="Remote whiteboarding was missing",
            solution_type="Online whiteboard",
            outcome=OutcomeType.UNICORN,
            outcome_value="$17.5B",
            year_founded=2011,
            signals=["whiteboard", "collaborate", "brainstorm", "remote", "visual", "diagram"],
            target_audience="Teams",
            key_differentiator="Infinite canvas collaboration",
        ),

        # Marketing & Sales
        SuccessPattern(
            name="HubSpot",
            category=Category.MARKETING,
            original_pain="Marketing tools were fragmented",
            solution_type="Inbound marketing platform",
            outcome=OutcomeType.IPO,
            outcome_value="$25B+",
            year_founded=2006,
            signals=["marketing", "crm", "inbound", "leads", "email", "automation"],
            target_audience="SMBs",
            key_differentiator="All-in-one marketing + CRM",
        ),
        SuccessPattern(
            name="Mailchimp",
            category=Category.MARKETING,
            original_pain="Email marketing was expensive and complex",
            solution_type="Email marketing",
            outcome=OutcomeType.ACQUISITION,
            outcome_value="$12B",
            year_founded=2001,
            signals=["email", "newsletter", "marketing", "campaign", "subscriber"],
            target_audience="Small businesses",
            key_differentiator="Free tier and simplicity",
        ),
        SuccessPattern(
            name="Gong",
            category=Category.SALES,
            original_pain="Sales call insights were manual",
            solution_type="Revenue intelligence",
            outcome=OutcomeType.UNICORN,
            outcome_value="$7.2B",
            year_founded=2015,
            signals=["sales", "call", "recording", "ai", "insights", "coaching"],
            target_audience="Sales teams",
            key_differentiator="AI-powered call analysis",
        ),

        # Analytics
        SuccessPattern(
            name="Amplitude",
            category=Category.ANALYTICS,
            original_pain="Product analytics was complex",
            solution_type="Product analytics",
            outcome=OutcomeType.IPO,
            outcome_value="$4B peak",
            year_founded=2012,
            signals=["analytics", "product", "user", "behavior", "retention", "funnel"],
            target_audience="Product teams",
            key_differentiator="Behavioral analytics",
        ),
        SuccessPattern(
            name="Mixpanel",
            category=Category.ANALYTICS,
            original_pain="Event tracking was hard to set up",
            solution_type="Event analytics",
            outcome=OutcomeType.UNICORN,
            outcome_value="$1B+",
            year_founded=2009,
            signals=["analytics", "event", "track", "user", "data", "metrics"],
            target_audience="Product teams",
            key_differentiator="Event-based analytics",
        ),

        # No-Code
        SuccessPattern(
            name="Webflow",
            category=Category.NO_CODE,
            original_pain="Building websites required coding",
            solution_type="Visual website builder",
            outcome=OutcomeType.UNICORN,
            outcome_value="$4B",
            year_founded=2013,
            signals=["website", "no-code", "design", "build", "cms", "visual"],
            target_audience="Designers",
            key_differentiator="Designer-level control without code",
        ),
        SuccessPattern(
            name="Zapier",
            category=Category.NO_CODE,
            original_pain="Connecting apps required developers",
            solution_type="App integration platform",
            outcome=OutcomeType.UNICORN,
            outcome_value="$5B",
            year_founded=2011,
            signals=["automation", "integrate", "connect", "workflow", "zap", "trigger"],
            target_audience="Business users",
            key_differentiator="No-code integrations",
        ),
        SuccessPattern(
            name="Retool",
            category=Category.NO_CODE,
            original_pain="Internal tools took too long to build",
            solution_type="Internal tool builder",
            outcome=OutcomeType.UNICORN,
            outcome_value="$3.2B",
            year_founded=2017,
            signals=["internal", "tool", "admin", "dashboard", "build", "database"],
            target_audience="Developers",
            key_differentiator="Fast internal tool building",
        ),

        # Security & Infrastructure
        SuccessPattern(
            name="Cloudflare",
            category=Category.SECURITY,
            original_pain="CDN and security were expensive",
            solution_type="CDN + Security",
            outcome=OutcomeType.IPO,
            outcome_value="$30B+",
            year_founded=2009,
            signals=["cdn", "security", "ddos", "dns", "performance", "edge"],
            target_audience="Websites and apps",
            key_differentiator="Free tier + easy setup",
        ),
        SuccessPattern(
            name="1Password",
            category=Category.SECURITY,
            original_pain="Password management was insecure",
            solution_type="Password manager",
            outcome=OutcomeType.UNICORN,
            outcome_value="$6.8B",
            year_founded=2006,
            signals=["password", "security", "login", "vault", "2fa", "credential"],
            target_audience="Individuals and teams",
            key_differentiator="Family and team sharing",
        ),

        # HR & Recruiting
        SuccessPattern(
            name="Gusto",
            category=Category.HR,
            original_pain="Payroll was complex for small businesses",
            solution_type="Payroll platform",
            outcome=OutcomeType.UNICORN,
            outcome_value="$10B",
            year_founded=2011,
            signals=["payroll", "hr", "benefits", "employee", "small business"],
            target_audience="Small businesses",
            key_differentiator="Simple payroll + HR",
        ),
        SuccessPattern(
            name="Deel",
            category=Category.HR,
            original_pain="Hiring internationally was complex",
            solution_type="Global payroll/hiring",
            outcome=OutcomeType.UNICORN,
            outcome_value="$12B",
            year_founded=2019,
            signals=["remote", "global", "hire", "contractor", "payroll", "international"],
            target_audience="Remote-first companies",
            key_differentiator="Global hiring compliance",
        ),

        # E-commerce
        SuccessPattern(
            name="Shopify",
            category=Category.ECOMMERCE,
            original_pain="Starting an online store was hard",
            solution_type="E-commerce platform",
            outcome=OutcomeType.IPO,
            outcome_value="$150B+ peak",
            year_founded=2006,
            signals=["store", "ecommerce", "sell", "online", "shop", "product"],
            target_audience="Merchants",
            key_differentiator="Easy store setup",
        ),
        SuccessPattern(
            name="Gumroad",
            category=Category.ECOMMERCE,
            original_pain="Selling digital products was fragmented",
            solution_type="Digital product sales",
            outcome=OutcomeType.PROFITABLE,
            outcome_value="$100M+ GMV",
            year_founded=2011,
            signals=["sell", "digital", "creator", "ebook", "course", "product"],
            target_audience="Creators",
            key_differentiator="Simple creator commerce",
        ),

        # AI/ML
        SuccessPattern(
            name="Jasper",
            category=Category.AI_ML,
            original_pain="Writing marketing copy was slow",
            solution_type="AI copywriting",
            outcome=OutcomeType.UNICORN,
            outcome_value="$1.5B",
            year_founded=2021,
            signals=["ai", "writing", "copy", "content", "marketing", "generate"],
            target_audience="Marketers",
            key_differentiator="Marketing-focused AI writing",
        ),
        SuccessPattern(
            name="Grammarly",
            category=Category.AI_ML,
            original_pain="Writing mistakes went unnoticed",
            solution_type="Writing assistant",
            outcome=OutcomeType.UNICORN,
            outcome_value="$13B",
            year_founded=2009,
            signals=["writing", "grammar", "spelling", "check", "correct", "improve"],
            target_audience="Everyone who writes",
            key_differentiator="Real-time writing suggestions",
        ),
    ]

    def __init__(self):
        """Initialize pattern database."""
        self._patterns_by_category: dict[Category, list[SuccessPattern]] = {}
        for pattern in self.PATTERNS:
            if pattern.category not in self._patterns_by_category:
                self._patterns_by_category[pattern.category] = []
            self._patterns_by_category[pattern.category].append(pattern)

    def get_all_patterns(self) -> list[SuccessPattern]:
        """Get all success patterns."""
        return self.PATTERNS

    def get_by_category(self, category: Category) -> list[SuccessPattern]:
        """Get patterns by category."""
        return self._patterns_by_category.get(category, [])

    def get_all_signals(self) -> set[str]:
        """Get all unique signals across patterns."""
        signals = set()
        for pattern in self.PATTERNS:
            signals.update(pattern.signals)
        return signals

    def search_by_signals(self, signals: list[str]) -> list[tuple[SuccessPattern, int]]:
        """Search patterns by matching signals. Returns (pattern, match_count) tuples."""
        results = []
        signals_lower = [s.lower() for s in signals]

        for pattern in self.PATTERNS:
            pattern_signals_lower = [s.lower() for s in pattern.signals]
            matches = sum(1 for s in signals_lower if s in pattern_signals_lower)
            if matches > 0:
                results.append((pattern, matches))

        return sorted(results, key=lambda x: x[1], reverse=True)
