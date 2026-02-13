"""Niche database with sector-specific characteristics.

Defines 15+ niches with their keywords, pain points, successful examples,
market size, and growth rate for specialized opportunity analysis.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class NicheDefinition:
    """Definition of a business niche/sector."""

    id: str
    name: str
    description: str
    keywords: List[str]
    pain_points: List[str]
    successful_examples: List[str]
    market_size_billions: float  # Market size in billions USD
    growth_rate: float  # Annual growth rate percentage
    avg_deal_size: Optional[int]  # Average deal size in USD (B2B)
    common_business_models: List[str]
    target_customers: List[str]


# Define all niches
NICHES = [
    NicheDefinition(
        id="fintech",
        name="FinTech",
        description="Financial technology solutions for payments, banking, investing",
        keywords=[
            "payment", "banking", "fintech", "crypto", "wallet", "transaction",
            "stripe", "paypal", "credit card", "debit", "invoice", "billing",
            "accounting", "tax", "expense", "budgeting", "investing", "trading",
            "loan", "mortgage", "insurance", "blockchain", "defi", "financial"
        ],
        pain_points=[
            "High transaction fees",
            "Slow payment processing",
            "Complex compliance requirements",
            "Poor user experience in banking apps",
            "Lack of financial transparency",
            "Difficulty accessing credit",
            "Manual expense tracking",
            "Fraud and security concerns"
        ],
        successful_examples=[
            "Stripe", "Square", "Plaid", "Revolut", "Wise", "Robinhood",
            "Chime", "Brex", "Mercury", "Ramp"
        ],
        market_size_billions=179.0,
        growth_rate=23.0,
        avg_deal_size=50000,
        common_business_models=["Transaction fee", "Subscription", "Freemium"],
        target_customers=["SMBs", "Enterprises", "Consumers", "Developers"]
    ),

    NicheDefinition(
        id="healthtech",
        name="HealthTech",
        description="Digital health, telemedicine, wellness, and medical technology",
        keywords=[
            "health", "medical", "telemedicine", "wellness", "fitness",
            "doctor", "patient", "hospital", "clinic", "pharmacy",
            "mental health", "therapy", "meditation", "sleep", "nutrition",
            "diagnosis", "prescription", "healthcare", "electronic health record",
            "ehr", "emr", "telehealth", "wearable", "disease", "symptom"
        ],
        pain_points=[
            "Long wait times for appointments",
            "High healthcare costs",
            "Lack of access to specialists",
            "Poor patient-doctor communication",
            "Fragmented medical records",
            "Medication adherence issues",
            "Mental health stigma",
            "Difficulty tracking health metrics"
        ],
        successful_examples=[
            "Calm", "Headspace", "Teladoc", "Oscar Health", "Ro", "Hims",
            "Noom", "One Medical", "23andMe", "Livongo"
        ],
        market_size_billions=293.0,
        growth_rate=15.0,
        avg_deal_size=75000,
        common_business_models=["Subscription", "Per-visit fee", "Insurance"],
        target_customers=["Consumers", "Healthcare providers", "Employers"]
    ),

    NicheDefinition(
        id="edtech",
        name="EdTech",
        description="Education technology, online learning, and student tools",
        keywords=[
            "education", "learning", "course", "student", "teacher",
            "school", "university", "training", "tutoring", "homework",
            "study", "exam", "grade", "classroom", "online learning",
            "elearning", "mooc", "certification", "skill", "coding bootcamp",
            "language learning", "math", "reading", "curriculum"
        ],
        pain_points=[
            "Expensive traditional education",
            "Lack of personalized learning",
            "Student engagement issues",
            "Difficulty tracking progress",
            "Limited access to quality teachers",
            "Outdated curriculum",
            "Skills gap in job market",
            "Student loan debt"
        ],
        successful_examples=[
            "Coursera", "Udemy", "Duolingo", "Kahoot", "ClassDojo",
            "Quizlet", "Chegg", "Khan Academy", "Masterclass", "Skillshare"
        ],
        market_size_billions=106.0,
        growth_rate=19.0,
        avg_deal_size=30000,
        common_business_models=["Subscription", "Per-course fee", "Freemium"],
        target_customers=["Students", "Teachers", "Schools", "Professionals"]
    ),

    NicheDefinition(
        id="devtools",
        name="DevTools",
        description="Developer tools, APIs, infrastructure, and software development",
        keywords=[
            "developer", "api", "code", "github", "git", "deployment",
            "ci/cd", "testing", "debugging", "monitoring", "logging",
            "database", "cloud", "aws", "docker", "kubernetes", "devops",
            "infrastructure", "serverless", "microservices", "sdk", "cli",
            "ide", "vscode", "programming", "software development"
        ],
        pain_points=[
            "Complex deployment processes",
            "Slow build times",
            "Difficult debugging",
            "Poor documentation",
            "Vendor lock-in",
            "High infrastructure costs",
            "Security vulnerabilities",
            "Integration challenges"
        ],
        successful_examples=[
            "GitHub", "GitLab", "Vercel", "Netlify", "Heroku", "Datadog",
            "PlanetScale", "Supabase", "Railway", "Render"
        ],
        market_size_billions=29.0,
        growth_rate=22.0,
        avg_deal_size=25000,
        common_business_models=["Usage-based", "Subscription", "Freemium"],
        target_customers=["Developers", "Engineering teams", "Startups"]
    ),

    NicheDefinition(
        id="ecommerce",
        name="E-Commerce",
        description="Online retail, marketplaces, and commerce enablement",
        keywords=[
            "ecommerce", "shop", "store", "marketplace", "retail",
            "selling", "shopping", "cart", "checkout", "product",
            "inventory", "shopify", "amazon", "etsy", "order",
            "shipping", "fulfillment", "dropshipping", "merchant",
            "online store", "sales", "revenue", "customer"
        ],
        pain_points=[
            "High marketplace fees",
            "Complex inventory management",
            "Shipping costs and delays",
            "Customer acquisition costs",
            "Shopping cart abandonment",
            "Returns and refunds",
            "Payment processing fees",
            "Competition from big retailers"
        ],
        successful_examples=[
            "Shopify", "WooCommerce", "BigCommerce", "Faire", "Gumroad",
            "ConvertKit Commerce", "Podia", "Thinkific"
        ],
        market_size_billions=5500.0,
        growth_rate=14.0,
        avg_deal_size=20000,
        common_business_models=["Transaction fee", "Subscription", "Marketplace fee"],
        target_customers=["Merchants", "Creators", "SMBs"]
    ),

    NicheDefinition(
        id="saas",
        name="SaaS (General)",
        description="General software-as-a-service and business tools",
        keywords=[
            "saas", "software", "cloud", "platform", "tool",
            "productivity", "workflow", "automation", "integration",
            "business", "enterprise", "collaboration", "team",
            "app", "dashboard", "analytics", "crm", "erp"
        ],
        pain_points=[
            "Tool sprawl and context switching",
            "High software costs",
            "Poor integrations",
            "Data silos",
            "Onboarding friction",
            "Lack of customization",
            "Vendor lock-in",
            "Security concerns"
        ],
        successful_examples=[
            "Slack", "Notion", "Airtable", "Monday.com", "ClickUp",
            "Zendesk", "HubSpot", "Salesforce"
        ],
        market_size_billions=186.0,
        growth_rate=18.0,
        avg_deal_size=40000,
        common_business_models=["Subscription", "Freemium", "Usage-based"],
        target_customers=["SMBs", "Enterprises", "Teams"]
    ),

    NicheDefinition(
        id="ai_ml",
        name="AI/ML",
        description="Artificial intelligence, machine learning, and automation",
        keywords=[
            "ai", "artificial intelligence", "machine learning", "ml",
            "chatgpt", "gpt", "llm", "openai", "claude", "chatbot",
            "automation", "neural network", "deep learning", "nlp",
            "computer vision", "prediction", "model", "training",
            "inference", "embeddings", "vector database", "rag"
        ],
        pain_points=[
            "High cost of AI APIs",
            "Difficulty integrating AI",
            "Lack of AI expertise",
            "Data privacy concerns",
            "Model hallucinations",
            "Slow inference times",
            "Complex prompt engineering",
            "AI safety concerns"
        ],
        successful_examples=[
            "OpenAI", "Anthropic", "Hugging Face", "Replicate", "Midjourney",
            "Jasper", "Copy.ai", "Synthesia", "RunwayML"
        ],
        market_size_billions=136.0,
        growth_rate=37.0,
        avg_deal_size=60000,
        common_business_models=["Usage-based", "Subscription", "API credits"],
        target_customers=["Developers", "Enterprises", "Creators", "SMBs"]
    ),

    NicheDefinition(
        id="creator_economy",
        name="Creator Economy",
        description="Tools for content creators, influencers, and online personalities",
        keywords=[
            "creator", "influencer", "youtube", "twitch", "tiktok",
            "content", "video", "streaming", "podcast", "newsletter",
            "substack", "patreon", "membership", "fan", "audience",
            "monetization", "sponsorship", "brand deal", "affiliate",
            "social media", "instagram", "twitter", "creator tools"
        ],
        pain_points=[
            "Inconsistent income",
            "Platform algorithm changes",
            "Difficulty monetizing",
            "High platform fees",
            "Limited audience insights",
            "Content copyright issues",
            "Burnout and content creation pressure",
            "Managing multiple platforms"
        ],
        successful_examples=[
            "Patreon", "Substack", "Beehiiv", "Kit", "Gumroad",
            "Teachable", "Kajabi", "Circle", "Discord"
        ],
        market_size_billions=104.0,
        growth_rate=25.0,
        avg_deal_size=15000,
        common_business_models=["Transaction fee", "Subscription", "Freemium"],
        target_customers=["Creators", "Influencers", "Educators"]
    ),

    NicheDefinition(
        id="hr_tech",
        name="HR Tech",
        description="Human resources, recruiting, and workforce management",
        keywords=[
            "hr", "recruiting", "hiring", "talent", "applicant",
            "resume", "job", "career", "employee", "onboarding",
            "payroll", "benefits", "performance review", "engagement",
            "ats", "hris", "workforce", "remote work", "time tracking",
            "leave management", "compensation", "headcount"
        ],
        pain_points=[
            "Time-consuming hiring processes",
            "Poor candidate experience",
            "High employee turnover",
            "Manual payroll processing",
            "Compliance complexity",
            "Lack of employee engagement",
            "Difficult performance management",
            "Remote workforce challenges"
        ],
        successful_examples=[
            "Workday", "BambooHR", "Rippling", "Deel", "Remote",
            "Greenhouse", "Lever", "Lattice", "Carta", "Gusto"
        ],
        market_size_billions=30.0,
        growth_rate=12.0,
        avg_deal_size=35000,
        common_business_models=["Subscription", "Per-employee fee"],
        target_customers=["SMBs", "Enterprises", "HR teams"]
    ),

    NicheDefinition(
        id="legal_tech",
        name="LegalTech",
        description="Legal services, contract management, and compliance",
        keywords=[
            "legal", "law", "lawyer", "contract", "agreement",
            "compliance", "regulation", "gdpr", "privacy", "terms",
            "litigation", "paralegal", "document review", "e-discovery",
            "legal research", "case management", "court", "filing"
        ],
        pain_points=[
            "High legal costs",
            "Slow contract review",
            "Manual document management",
            "Compliance complexity",
            "Inefficient legal research",
            "Poor contract visibility",
            "Risk of non-compliance",
            "Difficult cross-team collaboration"
        ],
        successful_examples=[
            "DocuSign", "PandaDoc", "IronClad", "Clio", "LegalZoom",
            "Rocket Lawyer", "Lex Machina", "Logikcull"
        ],
        market_size_billions=27.0,
        growth_rate=15.0,
        avg_deal_size=50000,
        common_business_models=["Subscription", "Per-document fee", "Freemium"],
        target_customers=["Law firms", "Enterprises", "SMBs", "Individuals"]
    ),

    NicheDefinition(
        id="proptech",
        name="PropTech",
        description="Property technology, real estate, and housing",
        keywords=[
            "real estate", "property", "housing", "rent", "lease",
            "landlord", "tenant", "apartment", "home", "house",
            "mortgage", "listing", "airbnb", "vacation rental",
            "property management", "facility", "building", "commercial real estate"
        ],
        pain_points=[
            "Complex property search",
            "High agent commissions",
            "Difficult tenant screening",
            "Manual rent collection",
            "Maintenance coordination",
            "Lease management complexity",
            "Limited property data",
            "Inefficient showings"
        ],
        successful_examples=[
            "Zillow", "Redfin", "Opendoor", "Airbnb", "Guesty",
            "Buildium", "AppFolio", "Rently", "Knock"
        ],
        market_size_billions=18.0,
        growth_rate=16.0,
        avg_deal_size=30000,
        common_business_models=["Transaction fee", "Subscription", "Commission"],
        target_customers=["Property managers", "Agents", "Landlords", "Renters"]
    ),

    NicheDefinition(
        id="foodtech",
        name="FoodTech",
        description="Food delivery, restaurant tech, and culinary innovation",
        keywords=[
            "food", "restaurant", "delivery", "menu", "order",
            "dining", "kitchen", "chef", "recipe", "meal",
            "grocery", "cooking", "pos", "reservation", "uber eats",
            "doordash", "grubhub", "catering", "food truck"
        ],
        pain_points=[
            "High delivery fees",
            "Slow order processing",
            "Inventory waste",
            "Staff scheduling issues",
            "Poor customer reviews",
            "Menu management complexity",
            "Payment processing delays",
            "Difficult reservation management"
        ],
        successful_examples=[
            "DoorDash", "Toast", "Square for Restaurants", "Olo",
            "ChowNow", "Resy", "OpenTable", "Grubhub"
        ],
        market_size_billions=151.0,
        growth_rate=11.0,
        avg_deal_size=20000,
        common_business_models=["Transaction fee", "Subscription", "Commission"],
        target_customers=["Restaurants", "Food businesses", "Consumers"]
    ),

    NicheDefinition(
        id="martech",
        name="MarTech",
        description="Marketing technology, advertising, and customer acquisition",
        keywords=[
            "marketing", "advertising", "seo", "sem", "email marketing",
            "campaign", "analytics", "conversion", "funnel", "attribution",
            "social media marketing", "content marketing", "influencer marketing",
            "ad", "google ads", "facebook ads", "retargeting", "growth"
        ],
        pain_points=[
            "High customer acquisition costs",
            "Poor campaign attribution",
            "Email deliverability issues",
            "Ad fatigue and declining ROI",
            "Difficulty measuring marketing ROI",
            "Complex marketing stack",
            "Data privacy restrictions",
            "Channel fragmentation"
        ],
        successful_examples=[
            "HubSpot", "Mailchimp", "Klaviyo", "Segment", "Mixpanel",
            "Amplitude", "Braze", "Iterable", "Customer.io"
        ],
        market_size_billions=344.0,
        growth_rate=17.0,
        avg_deal_size=45000,
        common_business_models=["Subscription", "Usage-based", "Freemium"],
        target_customers=["Marketing teams", "SMBs", "Enterprises", "Agencies"]
    ),

    NicheDefinition(
        id="productivity",
        name="Productivity",
        description="Personal productivity, time management, and organization",
        keywords=[
            "productivity", "task", "todo", "note", "organize",
            "calendar", "schedule", "reminder", "focus", "time tracking",
            "habit", "goal", "project management", "kanban", "wiki",
            "knowledge base", "second brain", "pkm"
        ],
        pain_points=[
            "Information overload",
            "Context switching",
            "Difficulty prioritizing tasks",
            "Poor time management",
            "Lack of focus",
            "Disconnected tools",
            "Forgotten tasks and deadlines",
            "Team coordination challenges"
        ],
        successful_examples=[
            "Notion", "Todoist", "Things", "Obsidian", "Roam Research",
            "Superhuman", "Asana", "Trello", "ClickUp"
        ],
        market_size_billions=85.0,
        growth_rate=13.0,
        avg_deal_size=15000,
        common_business_models=["Subscription", "Freemium", "One-time purchase"],
        target_customers=["Individuals", "Teams", "Knowledge workers"]
    ),

    NicheDefinition(
        id="security",
        name="Security/Cybersecurity",
        description="Cybersecurity, data protection, and privacy tools",
        keywords=[
            "security", "cybersecurity", "encryption", "privacy",
            "vpn", "password", "authentication", "2fa", "mfa",
            "firewall", "antivirus", "malware", "phishing", "breach",
            "vulnerability", "penetration testing", "soc", "siem",
            "zero trust", "identity", "access management"
        ],
        pain_points=[
            "Increasing cyber threats",
            "Complex compliance requirements",
            "Password management burden",
            "Data breach risks",
            "Insider threats",
            "Lack of security expertise",
            "Alert fatigue",
            "Budget constraints"
        ],
        successful_examples=[
            "1Password", "LastPass", "Okta", "Auth0", "Cloudflare",
            "CrowdStrike", "Snyk", "Vanta", "Drata"
        ],
        market_size_billions=173.0,
        growth_rate=12.0,
        avg_deal_size=75000,
        common_business_models=["Subscription", "Usage-based", "Enterprise licensing"],
        target_customers=["Enterprises", "SMBs", "Developers", "Individuals"]
    ),

    NicheDefinition(
        id="sales_tech",
        name="SalesTech",
        description="Sales enablement, CRM, and revenue operations",
        keywords=[
            "sales", "crm", "lead", "prospect", "pipeline",
            "deal", "quota", "revenue", "salesforce", "outreach",
            "cold email", "sales engagement", "account executive",
            "sdr", "bdr", "qualification", "forecasting", "commission"
        ],
        pain_points=[
            "Difficulty finding qualified leads",
            "Manual data entry",
            "Poor sales forecasting",
            "Slow deal cycles",
            "Lack of sales automation",
            "Inefficient follow-ups",
            "Commission calculation errors",
            "CRM adoption challenges"
        ],
        successful_examples=[
            "Salesforce", "HubSpot CRM", "Pipedrive", "Close",
            "Apollo", "Gong", "Chorus", "Outreach", "SalesLoft"
        ],
        market_size_billions=78.0,
        growth_rate=14.0,
        avg_deal_size=55000,
        common_business_models=["Subscription", "Usage-based", "Per-seat pricing"],
        target_customers=["Sales teams", "SMBs", "Enterprises"]
    ),
]


# Create lookup dictionary for fast access
NICHE_BY_ID = {niche.id: niche for niche in NICHES}


def get_niche(niche_id: str) -> Optional[NicheDefinition]:
    """Get niche definition by ID."""
    return NICHE_BY_ID.get(niche_id)


def get_all_niches() -> List[NicheDefinition]:
    """Get all niche definitions."""
    return NICHES


def get_niche_ids() -> List[str]:
    """Get list of all niche IDs."""
    return [niche.id for niche in NICHES]


def get_niche_names() -> List[str]:
    """Get list of all niche names."""
    return [niche.name for niche in NICHES]
