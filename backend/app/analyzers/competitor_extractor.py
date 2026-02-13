"""Competitor mention extraction and analysis.

Identifies mentions of competing SaaS products and analyzes sentiment.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class CompetitorSentiment(Enum):
    """Sentiment towards mentioned competitor."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    CHURNING = "churning"  # Actively leaving


@dataclass
class CompetitorMention:
    """A single competitor mention."""
    name: str
    category: str
    sentiment: CompetitorSentiment
    context: str
    is_churning: bool  # Explicitly leaving this competitor


@dataclass
class CompetitorExtractionResult:
    """Result of competitor extraction."""
    mentions: list[CompetitorMention]
    competitors_count: int
    has_churning: bool
    churning_from: list[str]
    categories: list[str]


class CompetitorExtractor:
    """Extracts and analyzes competitor mentions.

    Maintains a database of known SaaS products organized by category.
    Detects sentiment and churning signals.
    """

    # Known competitors by category
    COMPETITORS = {
        "project_management": [
            "asana", "monday", "monday.com", "trello", "jira", "basecamp",
            "clickup", "notion", "linear", "height", "shortcut", "wrike",
            "teamwork", "smartsheet", "airtable",
        ],
        "communication": [
            "slack", "teams", "microsoft teams", "discord", "zoom",
            "google meet", "loom", "whereby", "around", "tandem",
        ],
        "crm": [
            "salesforce", "hubspot", "pipedrive", "close", "copper",
            "freshsales", "zoho crm", "zendesk sell", "insightly",
        ],
        "email_marketing": [
            "mailchimp", "convertkit", "beehiiv", "substack", "buttondown",
            "sendgrid", "mailgun", "postmark", "sendinblue", "klaviyo",
            "drip", "activecampaign", "aweber", "constant contact",
        ],
        "analytics": [
            "google analytics", "mixpanel", "amplitude", "posthog",
            "heap", "fullstory", "hotjar", "logrocket", "plausible",
            "fathom", "simple analytics", "segment",
        ],
        "payments": [
            "stripe", "paypal", "square", "braintree", "paddle",
            "chargebee", "recurly", "gumroad", "lemonsqueezy",
        ],
        "auth": [
            "auth0", "okta", "clerk", "supabase auth", "firebase auth",
            "cognito", "stytch", "magic",
        ],
        "hosting": [
            "aws", "azure", "gcp", "google cloud", "vercel", "netlify",
            "heroku", "railway", "render", "fly.io", "digitalocean",
        ],
        "database": [
            "mongodb", "postgresql", "mysql", "supabase", "firebase",
            "planetscale", "neon", "fauna", "dynamodb", "redis",
        ],
        "design": [
            "figma", "sketch", "adobe xd", "canva", "framer",
            "invision", "zeplin", "abstract",
        ],
        "ai_tools": [
            "chatgpt", "claude", "midjourney", "dall-e", "stable diffusion",
            "jasper", "copy.ai", "writesonic", "grammarly", "notion ai",
        ],
        "video": [
            "youtube", "vimeo", "wistia", "vidyard", "loom",
            "descript", "riverside", "streamyard",
        ],
        "support": [
            "zendesk", "intercom", "freshdesk", "crisp", "helpscout",
            "drift", "tidio", "chatwoot",
        ],
        "forms": [
            "typeform", "google forms", "jotform", "tally", "paperform",
            "surveymonkey", "formspark",
        ],
        "scheduling": [
            "calendly", "cal.com", "savvycal", "doodle", "youcanbook.me",
            "acuity", "hubspot meetings",
        ],
        "no_code": [
            "bubble", "webflow", "framer", "carrd", "squarespace",
            "wix", "wordpress", "ghost", "typedream",
        ],
    }

    # Churning signal patterns
    CHURNING_PATTERNS = [
        r"(?:leaving|left|quitting|quit|ditching|ditched|dropping|dropped|abandoning|abandoned)\s+{competitor}",
        r"(?:switching|moved|moving|migrating|migrated)\s+(?:from|away from)\s+{competitor}",
        r"(?:cancell?ed|cancell?ing)\s+(?:my|our)?\s*{competitor}",
        r"{competitor}\s+(?:sucks|is terrible|is garbage|is awful|is trash)",
        r"(?:tired|sick|fed up)\s+(?:of|with)\s+{competitor}",
        r"(?:hate|hating|hated)\s+{competitor}",
        r"{competitor}\s+(?:pricing|prices)\s+(?:is|are)\s+(?:crazy|insane|ridiculous|too high)",
    ]

    # Negative sentiment patterns
    NEGATIVE_PATTERNS = [
        r"{competitor}\s+(?:doesn't|does not|won't|will not|can't|cannot)",
        r"(?:problem|issue|bug)s?\s+(?:with|in)\s+{competitor}",
        r"{competitor}\s+(?:is|was)\s+(?:slow|buggy|broken|down|unreliable)",
        r"(?:frustrated|annoyed|disappointed)\s+(?:with|by)\s+{competitor}",
    ]

    # Positive sentiment patterns
    POSITIVE_PATTERNS = [
        r"(?:love|loving|loved)\s+{competitor}",
        r"{competitor}\s+(?:is|was)\s+(?:great|amazing|awesome|excellent|perfect)",
        r"(?:recommend|recommending|recommended)\s+{competitor}",
        r"(?:happy|satisfied)\s+(?:with)\s+{competitor}",
    ]

    def __init__(self):
        """Initialize with compiled patterns."""
        # Build flat list of all competitors with their categories
        self._competitor_to_category = {}
        for category, competitors in self.COMPETITORS.items():
            for competitor in competitors:
                self._competitor_to_category[competitor.lower()] = category

        # Compile churning patterns (will be formatted per competitor)
        self._churning_patterns = [re.compile(p, re.IGNORECASE) for p in self.CHURNING_PATTERNS]
        self._negative_patterns = [re.compile(p, re.IGNORECASE) for p in self.NEGATIVE_PATTERNS]
        self._positive_patterns = [re.compile(p, re.IGNORECASE) for p in self.POSITIVE_PATTERNS]

    def extract(self, text: str) -> CompetitorExtractionResult:
        """Extract competitor mentions from text.

        Args:
            text: Text to analyze

        Returns:
            CompetitorExtractionResult with all findings
        """
        if not text:
            return CompetitorExtractionResult(
                mentions=[],
                competitors_count=0,
                has_churning=False,
                churning_from=[],
                categories=[]
            )

        text_lower = text.lower()
        mentions = []
        found_competitors = set()
        churning_from = []
        categories = set()

        for competitor, category in self._competitor_to_category.items():
            # Check if competitor is mentioned
            if competitor in text_lower:
                # Avoid partial matches (e.g., "notion" in "mention")
                pattern = rf"\b{re.escape(competitor)}\b"
                if not re.search(pattern, text_lower):
                    continue

                if competitor in found_competitors:
                    continue

                found_competitors.add(competitor)
                categories.add(category)

                # Analyze sentiment
                sentiment, is_churning = self._analyze_sentiment(text, competitor)

                # Get context
                context = self._get_context(text, competitor)

                mentions.append(CompetitorMention(
                    name=competitor,
                    category=category,
                    sentiment=sentiment,
                    context=context,
                    is_churning=is_churning
                ))

                if is_churning:
                    churning_from.append(competitor)

        return CompetitorExtractionResult(
            mentions=mentions,
            competitors_count=len(mentions),
            has_churning=len(churning_from) > 0,
            churning_from=churning_from,
            categories=list(categories)
        )

    def _analyze_sentiment(
        self,
        text: str,
        competitor: str
    ) -> tuple[CompetitorSentiment, bool]:
        """Analyze sentiment towards a competitor."""
        # Check churning patterns first (strongest signal)
        for pattern_template in self.CHURNING_PATTERNS:
            pattern = pattern_template.format(competitor=re.escape(competitor))
            if re.search(pattern, text, re.IGNORECASE):
                return CompetitorSentiment.CHURNING, True

        # Check negative patterns
        for pattern_template in self.NEGATIVE_PATTERNS:
            pattern = pattern_template.format(competitor=re.escape(competitor))
            if re.search(pattern, text, re.IGNORECASE):
                return CompetitorSentiment.NEGATIVE, False

        # Check positive patterns
        for pattern_template in self.POSITIVE_PATTERNS:
            pattern = pattern_template.format(competitor=re.escape(competitor))
            if re.search(pattern, text, re.IGNORECASE):
                return CompetitorSentiment.POSITIVE, False

        return CompetitorSentiment.NEUTRAL, False

    def _get_context(self, text: str, competitor: str) -> str:
        """Get surrounding context for competitor mention."""
        match = re.search(rf"\b{re.escape(competitor)}\b", text, re.IGNORECASE)
        if not match:
            return ""

        start = max(0, match.start() - 50)
        end = min(len(text), match.end() + 50)
        return text[start:end].strip()

    def get_category_description(self, category: str) -> str:
        """Get human-readable category description."""
        descriptions = {
            "project_management": "Project Management",
            "communication": "Communication & Chat",
            "crm": "CRM & Sales",
            "email_marketing": "Email Marketing",
            "analytics": "Analytics & Tracking",
            "payments": "Payments & Billing",
            "auth": "Authentication",
            "hosting": "Hosting & Infrastructure",
            "database": "Database",
            "design": "Design Tools",
            "ai_tools": "AI Tools",
            "video": "Video",
            "support": "Customer Support",
            "forms": "Forms & Surveys",
            "scheduling": "Scheduling",
            "no_code": "No-Code / Website Builders",
        }
        return descriptions.get(category, category.replace("_", " ").title())
