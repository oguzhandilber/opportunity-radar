"""AI client adapter - uses Ollama for smart local analysis."""

import json
import logging
import asyncio
import re
from abc import ABC, abstractmethod

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Ollama configuration
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "deepseek-r1:14b"  # Lightest available model


class BaseAIClient(ABC):
    """Base class for AI clients."""

    @abstractmethod
    async def complete(self, prompt: str, system: str | None = None) -> str:
        pass

    @abstractmethod
    async def complete_json(self, prompt: str, system: str | None = None) -> dict:
        pass

    @abstractmethod
    async def analyze_opportunity(self, content: str, source: str = "unknown") -> dict:
        """Analyze content and extract business opportunity information."""
        pass

    @abstractmethod
    async def deep_analysis(self, content: str, title: str) -> dict:
        """Deep analysis for detailed market/competitor insights."""
        pass

    @abstractmethod
    async def analyze_comment_sentiment(self, comment: str) -> dict:
        """Analyze comment sentiment - detect complaints, suggestions, praise."""
        pass

    @abstractmethod
    async def compare_competitors(self, opportunity: str, competitors: list) -> dict:
        """Compare competitors for a given opportunity with SWOT analysis."""
        pass

    @abstractmethod
    async def define_mvp(self, opportunity: dict) -> dict:
        """Define MVP features, effort, and tech stack for an opportunity."""
        pass

    @abstractmethod
    async def analyze_trend(self, posts: list) -> dict:
        """Analyze trends and patterns from a list of posts."""
        pass

    @abstractmethod
    async def calculate_market_size(self, opportunity: dict) -> dict:
        """Calculate TAM/SAM/SOM for an opportunity."""
        pass

    @abstractmethod
    async def generate_validation_plan(self, opportunity: dict) -> dict:
        """Generate 48-hour MVP validation plan with experiments."""
        pass

    @abstractmethod
    async def analyze_skill_requirements(self, opportunity: dict) -> dict:
        """Analyze required skills and technologies to build this opportunity.

        Returns skills, tech stack, learning path, and solo-friendliness assessment.
        """
        pass


class OpenRouterClient(BaseAIClient):
    """OpenRouter API client - access to free powerful models like DeepSeek R1 671B."""

    def __init__(self):
        self.api_key = settings.openrouter_api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = settings.openrouter_model
        self.fallback_model = settings.openrouter_fallback_model
        self.fallback = LocalAnalyzer()

    def _clean_think_tags(self, response: str) -> str:
        """Remove <think> tags from DeepSeek R1 responses."""
        if "<think>" in response:
            think_end = response.find("</think>")
            if think_end != -1:
                response = response[think_end + 8 :].strip()
        return response

    async def complete(self, prompt: str, system: str | None = None) -> str:
        """Generate completion using OpenRouter."""
        try:
            return await self._api_complete(prompt, system, self.model)
        except Exception as e:
            logger.warning(f"OpenRouter primary model error: {e}")
            try:
                return await self._api_complete(prompt, system, self.fallback_model)
            except Exception as e2:
                logger.warning(f"OpenRouter fallback error, using local: {e2}")
                return await self.fallback.complete(prompt, system)

    async def _api_complete(self, prompt: str, system: str | None, model: str) -> str:
        async with httpx.AsyncClient() as client:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://opportunity-radar.local",
                    "X-Title": "Opportunity Radar",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 8192,
                },
                timeout=180.0,
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return self._clean_think_tags(content)

    async def complete_json(self, prompt: str, system: str | None = None) -> dict:
        """Generate JSON using OpenRouter."""
        try:
            json_system = (
                (system or "")
                + "\n\nYou MUST respond with valid JSON only. No explanations, no markdown, just the JSON object."
            )
            response = await self.complete(prompt, json_system)
            response = response.strip()

            # Extract JSON from markdown code blocks
            if "```" in response:
                json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", response)
                if json_match:
                    response = json_match.group(1).strip()

            # Try to find JSON object in response
            json_match = re.search(r"\{[\s\S]*\}", response)
            if json_match:
                response = json_match.group(0)

            return json.loads(response)
        except Exception as e:
            logger.warning(f"OpenRouter JSON error ({e}), using fallback")
            return await self.fallback.complete_json(prompt, system)

    async def analyze_opportunity(self, content: str, source: str = "unknown") -> dict:
        """Smart opportunity analysis using LLM."""
        prompt = f"""Analyze this content from {source} and extract business opportunity information.

CONTENT:
{content[:4000]}

Respond with a JSON object containing:
{{
    "is_opportunity": true/false (is this a potential business opportunity?),
    "title": "short descriptive title for the opportunity",
    "summary": "2-3 sentence summary of the opportunity",
    "product_type": "SaaS" | "Mobile App" | "Chrome Extension" | "API" | "Telegram Bot" | "AI Agent" | "Other",
    "sector": "Fintech" | "Health" | "Education" | "Productivity" | "E-commerce" | "Marketing" | "HR" | "Developer Tools" | "Entertainment" | "Other",
    "business_model": "Subscription" | "Freemium" | "One-time" | "Transaction fee" | "Advertising",
    "demand_score": 1-10 (how strong is the demand signal?),
    "market_score": 1-10 (how big is the market potential?),
    "feasibility_score": 1-10 (how feasible for a solo developer?),
    "revenue_score": 1-10 (how clear is the monetization path?),
    "confidence": 0.0-1.0 (how confident are you in this analysis?),
    "competitors": ["list", "of", "known", "competitors"],
    "key_features": ["feature1", "feature2", "feature3"],
    "why_opportunity": "one sentence explaining why this is an opportunity"
}}

Be realistic and critical. Not everything is a good opportunity."""

        result = await self.complete_json(prompt)

        # Calculate total score
        if "demand_score" in result:
            scores = [
                result.get("demand_score", 5) * 1.5,
                result.get("market_score", 5),
                result.get("feasibility_score", 5) * 1.5,
                result.get("revenue_score", 5),
            ]
            result["total_score"] = round(sum(scores) / 5, 2)

        return result

    async def deep_analysis(self, content: str, title: str) -> dict:
        """Deep analysis for when user clicks 'Start Working'."""
        prompt = f"""You are a business analyst. Do a deep analysis of this business opportunity.

TITLE: {title}

CONTENT:
{content[:6000]}

Provide a detailed JSON response:
{{
    "market_analysis": {{
        "target_audience": "who would use this?",
        "market_size": "estimated market size and growth",
        "trends": ["relevant trends"]
    }},
    "competitors": [
        {{"name": "competitor name", "url": "website if known", "strengths": "what they do well", "weaknesses": "where they fail"}}
    ],
    "suggested_features": [
        {{"feature": "feature name", "priority": "high/medium/low", "description": "what it does", "effort": "days to build"}}
    ],
    "go_to_market": {{
        "strategy": "overall approach",
        "channels": ["marketing channels"],
        "first_steps": ["step1", "step2", "step3"]
    }},
    "risks": ["risk1", "risk2"],
    "turkey_fit": "how suitable is this for Turkish market?"
}}"""

        return await self.complete_json(prompt)

    async def analyze_comment_sentiment(self, comment: str) -> dict:
        """Analyze comment sentiment - detect complaints, suggestions, praise."""
        prompt = f"""Analyze this user comment and extract sentiment information.

COMMENT:
{comment[:2000]}

Respond with JSON:
{{
    "sentiment": "complaint" | "suggestion" | "praise" | "question" | "neutral",
    "pain_level": 1-10 (how frustrated is the user?),
    "willingness_to_pay": 1-10 (would they pay for a solution?),
    "urgency": 1-10 (how urgent is their need?),
    "key_problem": "one sentence describing their main problem",
    "desired_solution": "what they actually want"
}}"""

        return await self.complete_json(prompt)

    async def compare_competitors(self, opportunity: str, competitors: list) -> dict:
        """Compare competitors for a given opportunity."""
        prompt = f"""Analyze this business opportunity and compare it with existing competitors.

OPPORTUNITY:
{opportunity[:2000]}

KNOWN COMPETITORS:
{", ".join(competitors[:10])}

Provide a detailed JSON response:
{{
    "swot": {{
        "strengths": ["potential strengths of a new entrant"],
        "weaknesses": ["potential weaknesses"],
        "opportunities": ["market opportunities"],
        "threats": ["competitive threats"]
    }},
    "competitor_analysis": [
        {{"name": "competitor", "pricing": "their pricing model", "gap": "what they're missing"}}
    ],
    "differentiation_strategies": ["strategy1", "strategy2", "strategy3"],
    "recommended_positioning": "how to position against competitors"
}}"""

        return await self.complete_json(prompt)

    async def define_mvp(self, opportunity: dict) -> dict:
        """Define MVP for an opportunity."""
        prompt = f"""Based on this opportunity analysis, define an MVP (Minimum Viable Product).

OPPORTUNITY:
{json.dumps(opportunity, indent=2)[:3000]}

Respond with JSON:
{{
    "mvp_name": "suggested product name",
    "core_features": [
        {{"feature": "name", "description": "what it does", "priority": 1-5, "effort_days": estimated days}}
    ],
    "total_effort_days": total days to build MVP,
    "tech_stack": {{
        "frontend": "recommended frontend",
        "backend": "recommended backend",
        "database": "recommended database",
        "hosting": "recommended hosting"
    }},
    "launch_checklist": ["step1", "step2", "step3"],
    "success_metrics": ["metric1", "metric2"]
}}"""

        return await self.complete_json(prompt)

    async def analyze_trend(self, posts: list) -> dict:
        """Analyze trends from a list of posts."""
        posts_text = "\n---\n".join(
            [p.get("title", "") + ": " + p.get("content", "")[:200] for p in posts[:20]]
        )

        prompt = f"""Analyze these posts to identify trends and patterns.

POSTS:
{posts_text[:4000]}

Respond with JSON:
{{
    "main_theme": "overall theme of these posts",
    "sub_themes": ["theme1", "theme2", "theme3"],
    "trend_direction": "growing" | "stable" | "declining",
    "trend_strength": 1-10,
    "seasonality": "is this seasonal? explain",
    "predicted_growth": "short term prediction",
    "opportunity_summary": "what opportunity does this trend present?"
}}"""

        return await self.complete_json(prompt)

    async def calculate_market_size(self, opportunity: dict) -> dict:
        """Calculate TAM/SAM/SOM for an opportunity."""
        prompt = f"""You are a market research analyst. Calculate the market size for this opportunity.

OPPORTUNITY:
{json.dumps(opportunity, indent=2)[:3000]}

Provide a detailed JSON response with realistic estimates:
{{
    "tam": {{
        "value": "Total Addressable Market in USD (e.g., $50B)",
        "description": "Everyone who could potentially use this product globally",
        "calculation": "How you arrived at this number"
    }},
    "sam": {{
        "value": "Serviceable Addressable Market in USD (e.g., $5B)",
        "description": "The portion of TAM you can realistically target",
        "calculation": "How you arrived at this number"
    }},
    "som": {{
        "value": "Serviceable Obtainable Market in USD (e.g., $50M)",
        "description": "Realistic market share you can capture in 1-3 years",
        "calculation": "How you arrived at this number"
    }},
    "market_growth_rate": "Annual growth rate percentage",
    "key_assumptions": ["assumption1", "assumption2"],
    "comparable_companies": [
        {{"name": "company", "valuation": "their valuation/revenue", "market_share": "estimated share"}}
    ],
    "confidence_level": "low/medium/high",
    "data_sources": ["source1", "source2"]
}}

Be realistic and conservative. Use available market data and comparable companies."""

        return await self.complete_json(prompt)

    async def generate_validation_plan(self, opportunity: dict) -> dict:
        """Generate 48-hour MVP validation plan with experiments."""
        prompt = f"""You are a lean startup expert. Create a 48-hour validation plan for this opportunity.

OPPORTUNITY:
{json.dumps(opportunity, indent=2)[:3000]}

Provide a detailed JSON response:
{{
    "validation_goal": "What we're trying to validate in 48 hours",
    "hypothesis": "The core assumption we need to test",
    "success_criteria": "How we'll know if validation is successful",

    "hour_by_hour_plan": [
        {{"hours": "0-4", "task": "task description", "deliverable": "what you'll have"}},
        {{"hours": "4-8", "task": "task description", "deliverable": "what you'll have"}},
        {{"hours": "8-16", "task": "task description", "deliverable": "what you'll have"}},
        {{"hours": "16-24", "task": "task description", "deliverable": "what you'll have"}},
        {{"hours": "24-36", "task": "task description", "deliverable": "what you'll have"}},
        {{"hours": "36-48", "task": "task description", "deliverable": "what you'll have"}}
    ],

    "landing_page": {{
        "headline_options": ["option1", "option2", "option3"],
        "value_propositions": ["vp1", "vp2", "vp3"],
        "cta_options": ["cta1", "cta2"],
        "recommended_tool": "Carrd/Webflow/etc"
    }},

    "quick_experiments": [
        {{
            "experiment": "name",
            "description": "what to do",
            "success_metric": "how to measure",
            "time_needed": "hours"
        }}
    ],

    "survey_questions": [
        "question1?",
        "question2?",
        "question3?"
    ],

    "where_to_find_users": [
        {{"platform": "Reddit/Twitter/etc", "specific_location": "subreddit/hashtag", "approach": "how to engage"}}
    ],

    "minimum_validation_signals": {{
        "email_signups": "target number",
        "survey_responses": "target number",
        "positive_feedback_ratio": "target percentage"
    }},

    "go_no_go_decision": "Clear criteria for deciding to proceed or pivot"
}}

Focus on speed and actionable steps. No coding required in first 48 hours."""

        return await self.complete_json(prompt)

    async def analyze_skill_requirements(self, opportunity: dict) -> dict:
        """Analyze required skills and technologies to build this opportunity."""
        prompt = f"""You are a senior technical architect. Analyze the skills and technologies needed to build this product.

OPPORTUNITY:
{json.dumps(opportunity, indent=2)[:3000]}

Provide a detailed JSON response:
{{
    "required_skills": [
        {{
            "skill": "skill name",
            "category": "frontend" | "backend" | "database" | "devops" | "design" | "marketing" | "domain",
            "level": "beginner" | "intermediate" | "advanced",
            "importance": "critical" | "important" | "nice_to_have",
            "learning_time_days": estimated days to learn from scratch
        }}
    ],

    "recommended_stack": {{
        "frontend": {{"tech": "React/Vue/etc", "reason": "why this choice"}},
        "backend": {{"tech": "Python/Node/etc", "reason": "why this choice"}},
        "database": {{"tech": "PostgreSQL/MongoDB/etc", "reason": "why this choice"}},
        "hosting": {{"tech": "Vercel/Railway/etc", "reason": "why this choice"}},
        "additional_services": [{{"service": "Stripe/Auth0/etc", "purpose": "what it does"}}]
    }},

    "solo_friendly": {{
        "verdict": true/false,
        "score": 1-10 (how suitable for a solo developer),
        "reasoning": "explain why",
        "bottlenecks": ["potential solo dev challenges"]
    }},

    "mvp_complexity": {{
        "level": "low" | "medium" | "high",
        "estimated_hours": {{
            "beginner": hours for beginner,
            "intermediate": hours for intermediate dev,
            "expert": hours for expert
        }},
        "complexity_factors": ["what makes it complex or simple"]
    }},

    "nocode_alternative": {{
        "possible": true/false,
        "recommended_tools": ["Bubble", "Webflow", etc],
        "limitations": ["what you can't do with no-code"],
        "time_savings": "percentage faster than coding"
    }},

    "learning_path": [
        {{
            "skill": "skill to learn",
            "priority": 1-5 (1 = learn first),
            "resources": ["recommended learning resources"],
            "time_days": estimated days
        }}
    ],

    "team_recommendation": {{
        "min_team_size": 1-5,
        "ideal_team_size": 1-5,
        "roles_needed": ["role1", "role2"],
        "can_outsource": ["tasks that can be outsourced"]
    }},

    "risk_assessment": {{
        "technical_risks": ["risk1", "risk2"],
        "skill_gaps": ["most challenging skill areas"],
        "mitigation_strategies": ["how to reduce risks"]
    }}
}}

Be realistic about skill requirements. Consider both building AND maintaining the product."""

        return await self.complete_json(prompt)


class OllamaClient(BaseAIClient):
    """Ollama local LLM client for smart analysis."""

    def __init__(self, model: str = OLLAMA_MODEL):
        self.model = model
        self.base_url = OLLAMA_BASE_URL
        self.fallback = LocalAnalyzer()

    async def complete(self, prompt: str, system: str | None = None) -> str:
        """Generate completion using Ollama."""
        try:
            return await self._api_complete(prompt, system)
        except Exception as e:
            logger.warning(f"Ollama error, using fallback: {e}")
            return await self.fallback.complete(prompt, system)

    async def _api_complete(self, prompt: str, system: str | None = None) -> str:
        async with httpx.AsyncClient() as client:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
            }
            if system:
                payload["system"] = system

            response = await client.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=120.0,  # LLM can be slow
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")

    async def complete_json(self, prompt: str, system: str | None = None) -> dict:
        """Generate JSON using Ollama."""
        try:
            json_system = (
                (system or "")
                + "\n\nYou MUST respond with valid JSON only. No explanations, no markdown, just the JSON object."
            )
            response = await self._api_complete(prompt, json_system)

            # Clean response - extract JSON from possible markdown or text
            response = response.strip()

            # Remove thinking tags if present (deepseek-r1 uses these)
            if "<think>" in response:
                think_end = response.find("</think>")
                if think_end != -1:
                    response = response[think_end + 8 :].strip()

            # Extract JSON from markdown code blocks
            if "```" in response:
                # Find JSON block
                json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", response)
                if json_match:
                    response = json_match.group(1).strip()

            # Try to find JSON object in response
            json_match = re.search(r"\{[\s\S]*\}", response)
            if json_match:
                response = json_match.group(0)

            return json.loads(response)
        except Exception as e:
            logger.warning(f"Ollama JSON error ({e}), using fallback")
            return await self.fallback.complete_json(prompt, system)

    async def analyze_opportunity(self, content: str, source: str = "unknown") -> dict:
        """Smart opportunity analysis using LLM."""
        prompt = f"""Analyze this content from {source} and extract business opportunity information.

CONTENT:
{content[:2000]}

Respond with a JSON object containing:
{{
    "is_opportunity": true/false (is this a potential business opportunity?),
    "title": "short descriptive title for the opportunity",
    "summary": "2-3 sentence summary of the opportunity",
    "product_type": "SaaS" | "Mobile App" | "Chrome Extension" | "API" | "Telegram Bot" | "AI Agent" | "Other",
    "sector": "Fintech" | "Health" | "Education" | "Productivity" | "E-commerce" | "Marketing" | "HR" | "Developer Tools" | "Entertainment" | "Other",
    "business_model": "Subscription" | "Freemium" | "One-time" | "Transaction fee" | "Advertising",
    "demand_score": 1-10 (how strong is the demand signal?),
    "market_score": 1-10 (how big is the market potential?),
    "feasibility_score": 1-10 (how feasible for a solo developer?),
    "revenue_score": 1-10 (how clear is the monetization path?),
    "confidence": 0.0-1.0 (how confident are you in this analysis?),
    "competitors": ["list", "of", "known", "competitors"],
    "key_features": ["feature1", "feature2", "feature3"],
    "why_opportunity": "one sentence explaining why this is an opportunity"
}}

Be realistic and critical. Not everything is a good opportunity."""

        result = await self.complete_json(prompt)

        # Calculate total score
        if "demand_score" in result:
            scores = [
                result.get("demand_score", 5) * 1.5,
                result.get("market_score", 5),
                result.get("feasibility_score", 5) * 1.5,
                result.get("revenue_score", 5),
            ]
            result["total_score"] = round(sum(scores) / 5, 2)

        return result

    async def deep_analysis(self, content: str, title: str) -> dict:
        """Deep analysis for when user clicks 'Start Working'."""
        prompt = f"""You are a business analyst. Do a deep analysis of this business opportunity.

TITLE: {title}

CONTENT:
{content[:3000]}

Provide a detailed JSON response:
{{
    "market_analysis": {{
        "target_audience": "who would use this?",
        "market_size": "estimated market size and growth",
        "trends": ["relevant trends"]
    }},
    "competitors": [
        {{"name": "competitor name", "url": "website if known", "strengths": "what they do well", "weaknesses": "where they fail"}}
    ],
    "suggested_features": [
        {{"feature": "feature name", "priority": "high/medium/low", "description": "what it does", "effort": "days to build"}}
    ],
    "go_to_market": {{
        "strategy": "overall approach",
        "channels": ["marketing channels"],
        "first_steps": ["step1", "step2", "step3"]
    }},
    "risks": ["risk1", "risk2"],
    "turkey_fit": "how suitable is this for Turkish market?"
}}"""

        return await self.complete_json(prompt)

    async def analyze_comment_sentiment(self, comment: str) -> dict:
        """Analyze comment sentiment - detect complaints, suggestions, praise."""
        prompt = f"""Analyze this user comment and extract sentiment information.

COMMENT:
{comment[:2000]}

Respond with JSON:
{{
    "sentiment": "complaint" | "suggestion" | "praise" | "question" | "neutral",
    "pain_level": 1-10 (how frustrated is the user?),
    "willingness_to_pay": 1-10 (would they pay for a solution?),
    "urgency": 1-10 (how urgent is their need?),
    "key_problem": "one sentence describing their main problem",
    "desired_solution": "what they actually want"
}}"""

        return await self.complete_json(prompt)

    async def compare_competitors(self, opportunity: str, competitors: list) -> dict:
        """Compare competitors for a given opportunity."""
        prompt = f"""Analyze this business opportunity and compare it with existing competitors.

OPPORTUNITY:
{opportunity[:2000]}

KNOWN COMPETITORS:
{", ".join(competitors[:10])}

Provide a detailed JSON response:
{{
    "swot": {{
        "strengths": ["potential strengths of a new entrant"],
        "weaknesses": ["potential weaknesses"],
        "opportunities": ["market opportunities"],
        "threats": ["competitive threats"]
    }},
    "competitor_analysis": [
        {{"name": "competitor", "pricing": "their pricing model", "gap": "what they're missing"}}
    ],
    "differentiation_strategies": ["strategy1", "strategy2", "strategy3"],
    "recommended_positioning": "how to position against competitors"
}}"""

        return await self.complete_json(prompt)

    async def define_mvp(self, opportunity: dict) -> dict:
        """Define MVP for an opportunity."""
        prompt = f"""Based on this opportunity analysis, define an MVP (Minimum Viable Product).

OPPORTUNITY:
{json.dumps(opportunity, indent=2)[:3000]}

Respond with JSON:
{{
    "mvp_name": "suggested product name",
    "core_features": [
        {{"feature": "name", "description": "what it does", "priority": 1-5, "effort_days": estimated days}}
    ],
    "total_effort_days": total days to build MVP,
    "tech_stack": {{
        "frontend": "recommended frontend",
        "backend": "recommended backend",
        "database": "recommended database",
        "hosting": "recommended hosting"
    }},
    "launch_checklist": ["step1", "step2", "step3"],
    "success_metrics": ["metric1", "metric2"]
}}"""

        return await self.complete_json(prompt)

    async def analyze_trend(self, posts: list) -> dict:
        """Analyze trends from a list of posts."""
        posts_text = "\n---\n".join(
            [p.get("title", "") + ": " + p.get("content", "")[:200] for p in posts[:20]]
        )

        prompt = f"""Analyze these posts to identify trends and patterns.

POSTS:
{posts_text[:4000]}

Respond with JSON:
{{
    "main_theme": "overall theme of these posts",
    "sub_themes": ["theme1", "theme2", "theme3"],
    "trend_direction": "growing" | "stable" | "declining",
    "trend_strength": 1-10,
    "seasonality": "is this seasonal? explain",
    "predicted_growth": "short term prediction",
    "opportunity_summary": "what opportunity does this trend present?"
}}"""

        return await self.complete_json(prompt)

    async def calculate_market_size(self, opportunity: dict) -> dict:
        """Calculate TAM/SAM/SOM for an opportunity."""
        prompt = f"""Calculate market size for this opportunity.

OPPORTUNITY:
{json.dumps(opportunity, indent=2)[:2000]}

Respond with JSON:
{{
    "tam": {{"value": "$X", "description": "total market"}},
    "sam": {{"value": "$X", "description": "serviceable market"}},
    "som": {{"value": "$X", "description": "obtainable market"}},
    "market_growth_rate": "X%",
    "confidence_level": "low/medium/high"
}}"""
        return await self.complete_json(prompt)

    async def generate_validation_plan(self, opportunity: dict) -> dict:
        """Generate 48-hour MVP validation plan."""
        prompt = f"""Create a 48-hour validation plan for this opportunity.

OPPORTUNITY:
{json.dumps(opportunity, indent=2)[:2000]}

Respond with JSON:
{{
    "validation_goal": "what to validate",
    "hypothesis": "core assumption",
    "hour_by_hour_plan": [
        {{"hours": "0-12", "task": "task", "deliverable": "output"}},
        {{"hours": "12-24", "task": "task", "deliverable": "output"}},
        {{"hours": "24-48", "task": "task", "deliverable": "output"}}
    ],
    "landing_page": {{
        "headline_options": ["option1", "option2"],
        "recommended_tool": "Carrd"
    }},
    "where_to_find_users": ["location1", "location2"],
    "success_criteria": "how to know if validated"
}}"""
        return await self.complete_json(prompt)

    async def analyze_skill_requirements(self, opportunity: dict) -> dict:
        """Analyze required skills and technologies to build this opportunity."""
        prompt = f"""Analyze the skills and technologies needed to build this product.

OPPORTUNITY:
{json.dumps(opportunity, indent=2)[:2000]}

Respond with JSON:
{{
    "required_skills": [
        {{"skill": "name", "category": "frontend/backend/etc", "level": "beginner/intermediate/advanced"}}
    ],
    "recommended_stack": {{
        "frontend": "tech choice",
        "backend": "tech choice",
        "database": "tech choice"
    }},
    "solo_friendly": true/false,
    "mvp_complexity": "low/medium/high",
    "estimated_hours": number,
    "nocode_possible": true/false,
    "learning_path": ["skill1", "skill2"]
}}"""
        return await self.complete_json(prompt)


class LocalAnalyzer(BaseAIClient):
    """Local rule-based analyzer for when API is unavailable."""

    # Product type keywords
    PRODUCT_TYPES = {
        "SaaS": ["saas", "subscription", "cloud", "platform", "dashboard", "software"],
        "Mobile App": ["app", "mobile", "ios", "android", "phone"],
        "Chrome Extension": ["extension", "chrome", "browser", "plugin"],
        "API": ["api", "integration", "webhook", "endpoint"],
        "Telegram Bot": ["telegram", "bot", "chatbot"],
        "AI Agent": ["ai", "agent", "automation", "gpt", "llm"],
    }

    # Sector keywords
    SECTORS = {
        "Fintech": ["finance", "payment", "banking", "money", "investment", "crypto"],
        "Health": ["health", "medical", "fitness", "wellness", "doctor", "patient"],
        "Education": ["education", "learning", "course", "student", "teaching"],
        "Productivity": [
            "productivity",
            "workflow",
            "task",
            "project",
            "time",
            "calendar",
        ],
        "E-commerce": ["ecommerce", "shop", "store", "selling", "product", "inventory"],
        "Marketing": ["marketing", "seo", "ads", "social media", "content", "email"],
        "HR": ["hr", "hiring", "recruiting", "employee", "team", "talent"],
    }

    # Business model keywords
    BUSINESS_MODELS = {
        "Subscription": ["monthly", "subscription", "recurring", "plan"],
        "Freemium": ["free", "freemium", "trial", "premium"],
        "One-time": ["one-time", "lifetime", "purchase", "buy once"],
        "Transaction fee": ["commission", "fee", "transaction", "percentage"],
    }

    async def complete(self, prompt: str, system: str | None = None) -> str:
        return "Local analysis completed"

    async def complete_json(self, prompt: str, system: str | None = None) -> dict:
        # Extract content from prompt
        content = prompt.lower()

        # Try to determine what kind of analysis is needed
        if "classify" in prompt.lower() or "is_opportunity" in prompt.lower():
            return self._classify(content)
        elif "score" in prompt.lower():
            return self._score(content)
        elif "enrich" in prompt.lower() or "competitor" in prompt.lower():
            return self._enrich(content)

        return {}

    def _classify(self, content: str) -> dict:
        """Classify content as business opportunity."""
        # Detect product type
        product_type = "Other"
        for ptype, keywords in self.PRODUCT_TYPES.items():
            if any(kw in content for kw in keywords):
                product_type = ptype
                break

        # Detect sector
        sector = "Other"
        for sect, keywords in self.SECTORS.items():
            if any(kw in content for kw in keywords):
                sector = sect
                break

        # Detect business model
        business_model = "Subscription"  # Default
        for model, keywords in self.BUSINESS_MODELS.items():
            if any(kw in content for kw in keywords):
                business_model = model
                break

        # Extract title - look for the actual content after the prompt
        # Find "Content:" or just use first meaningful line
        content_start = content.find("content:")
        if content_start != -1:
            actual_content = content[content_start + 8 :].strip()
        else:
            actual_content = content

        # Get first line as title
        lines = [
            l.strip()
            for l in actual_content.split("\n")
            if l.strip() and len(l.strip()) > 10
        ]
        if lines:
            title = lines[0][:100]
        else:
            title = actual_content[:100]
        title = title.strip().title()

        return {
            "is_opportunity": True,
            "title": title,
            "summary": content[:300],
            "product_type": product_type,
            "sector": sector,
            "business_model": business_model,
        }

    def _score(self, content: str) -> dict:
        """Score opportunity based on keyword signals."""
        # Demand signals
        demand_keywords = [
            "need",
            "want",
            "looking for",
            "wish",
            "frustrated",
            "pay for",
            "would pay",
        ]
        demand_score = min(10, 4 + sum(2 for kw in demand_keywords if kw in content))

        # Market signals
        market_keywords = [
            "market",
            "growing",
            "trend",
            "popular",
            "millions",
            "industry",
        ]
        market_score = min(10, 4 + sum(1.5 for kw in market_keywords if kw in content))

        # Feasibility signals
        complexity_keywords = [
            "complex",
            "difficult",
            "hard",
            "regulatory",
            "compliance",
        ]
        feasibility_score = max(
            3, 8 - sum(1.5 for kw in complexity_keywords if kw in content)
        )

        # Revenue signals
        revenue_keywords = [
            "revenue",
            "profit",
            "monetize",
            "$",
            "pricing",
            "subscription",
        ]
        revenue_score = min(
            10, 4 + sum(1.5 for kw in revenue_keywords if kw in content)
        )

        total = (
            demand_score * 1.5 + market_score + feasibility_score * 1.5 + revenue_score
        ) / 5

        return {
            "demand_score": round(demand_score, 1),
            "market_score": round(market_score, 1),
            "feasibility_score": round(feasibility_score, 1),
            "revenue_score": round(revenue_score, 1),
            "total_score": round(total, 2),
            "confidence": 0.6,
        }

    def _enrich(self, content: str) -> dict:
        """Enrich with basic suggestions."""
        return {
            "competitors": [
                {"name": "Market Leader", "url": "", "notes": "Research needed"},
            ],
            "suggested_features": [
                {
                    "feature": "User Dashboard",
                    "priority": "high",
                    "description": "Main user interface",
                },
                {
                    "feature": "Authentication",
                    "priority": "high",
                    "description": "User login/signup",
                },
                {
                    "feature": "Core Functionality",
                    "priority": "high",
                    "description": "Main feature set",
                },
                {
                    "feature": "Notifications",
                    "priority": "medium",
                    "description": "Email/push alerts",
                },
                {
                    "feature": "Analytics",
                    "priority": "medium",
                    "description": "Usage tracking",
                },
            ],
            "go_to_market": "Start with a focused MVP targeting early adopters. Use content marketing and SEO to build organic traffic. Consider Product Hunt launch for initial visibility.",
        }

    async def analyze_opportunity(self, content: str, source: str = "unknown") -> dict:
        """Local rule-based opportunity analysis."""
        classification = self._classify(content)
        scores = self._score(content)
        return {**classification, **scores}

    async def deep_analysis(self, content: str, title: str) -> dict:
        """Local rule-based deep analysis."""
        return self._enrich(content)

    async def analyze_comment_sentiment(self, comment: str) -> dict:
        """Local rule-based sentiment analysis."""
        content = comment.lower()

        # Detect sentiment
        complaint_words = [
            "frustrated",
            "annoyed",
            "hate",
            "terrible",
            "awful",
            "broken",
            "useless",
        ]
        praise_words = ["love", "great", "amazing", "excellent", "perfect", "best"]
        suggestion_words = [
            "should",
            "could",
            "would be nice",
            "wish",
            "suggest",
            "recommend",
        ]
        question_words = ["how", "what", "why", "when", "where", "?"]

        sentiment = "neutral"
        if any(w in content for w in complaint_words):
            sentiment = "complaint"
        elif any(w in content for w in praise_words):
            sentiment = "praise"
        elif any(w in content for w in suggestion_words):
            sentiment = "suggestion"
        elif any(w in content for w in question_words):
            sentiment = "question"

        # Calculate pain level
        pain_words = [
            "frustrated",
            "annoyed",
            "hate",
            "terrible",
            "can't",
            "impossible",
            "broken",
        ]
        pain_level = min(10, 3 + sum(2 for w in pain_words if w in content))

        # Calculate willingness to pay
        pay_words = [
            "pay",
            "money",
            "worth",
            "budget",
            "$",
            "price",
            "cost",
            "subscribe",
        ]
        willingness_to_pay = min(10, 3 + sum(2 for w in pay_words if w in content))

        # Calculate urgency
        urgency_words = [
            "urgent",
            "asap",
            "immediately",
            "now",
            "quickly",
            "deadline",
            "need",
        ]
        urgency = min(10, 3 + sum(2 for w in urgency_words if w in content))

        return {
            "sentiment": sentiment,
            "pain_level": pain_level,
            "willingness_to_pay": willingness_to_pay,
            "urgency": urgency,
            "key_problem": "Analysis requires AI model",
            "desired_solution": "Analysis requires AI model",
        }

    async def compare_competitors(self, opportunity: str, competitors: list) -> dict:
        """Local rule-based competitor comparison."""
        return {
            "swot": {
                "strengths": [
                    "Fresh perspective",
                    "Modern technology stack",
                    "No legacy baggage",
                ],
                "weaknesses": [
                    "No brand recognition",
                    "Limited resources",
                    "New to market",
                ],
                "opportunities": ["Underserved niches", "Better UX", "Lower pricing"],
                "threats": [
                    "Established competitors",
                    "Market saturation",
                    "Changing regulations",
                ],
            },
            "competitor_analysis": [
                {"name": c, "pricing": "Unknown", "gap": "Research needed"}
                for c in competitors[:5]
            ],
            "differentiation_strategies": [
                "Focus on underserved niche",
                "Provide better customer support",
                "Offer simpler pricing",
            ],
            "recommended_positioning": "Position as a modern, user-friendly alternative with competitive pricing",
        }

    async def define_mvp(self, opportunity: dict) -> dict:
        """Local rule-based MVP definition."""
        return {
            "mvp_name": opportunity.get("title", "New Product"),
            "core_features": [
                {
                    "feature": "Authentication",
                    "description": "User login/signup",
                    "priority": 1,
                    "effort_days": 3,
                },
                {
                    "feature": "Core Feature",
                    "description": "Main functionality",
                    "priority": 1,
                    "effort_days": 10,
                },
                {
                    "feature": "Dashboard",
                    "description": "User interface",
                    "priority": 2,
                    "effort_days": 5,
                },
                {
                    "feature": "Settings",
                    "description": "User preferences",
                    "priority": 3,
                    "effort_days": 2,
                },
            ],
            "total_effort_days": 20,
            "tech_stack": {
                "frontend": "React + TypeScript",
                "backend": "FastAPI / Node.js",
                "database": "PostgreSQL",
                "hosting": "Railway / Vercel",
            },
            "launch_checklist": [
                "Set up development environment",
                "Build core features",
                "Deploy to staging",
                "Beta testing",
                "Launch on Product Hunt",
            ],
            "success_metrics": [
                "Number of signups",
                "Daily active users",
                "Conversion rate",
                "Customer satisfaction",
            ],
        }

    async def analyze_trend(self, posts: list) -> dict:
        """Local rule-based trend analysis."""
        return {
            "main_theme": "Analysis requires AI model",
            "sub_themes": ["Theme detection requires AI"],
            "trend_direction": "stable",
            "trend_strength": 5,
            "seasonality": "Unknown - requires AI analysis",
            "predicted_growth": "Unknown - requires AI analysis",
            "opportunity_summary": "AI-powered trend analysis provides more accurate insights",
        }

    async def calculate_market_size(self, opportunity: dict) -> dict:
        """Local rule-based market size estimation."""
        return {
            "tam": {
                "value": "$1B - $10B",
                "description": "Estimated based on sector averages",
                "calculation": "Requires AI for detailed calculation",
            },
            "sam": {
                "value": "$100M - $1B",
                "description": "Target market segment",
                "calculation": "Requires AI for detailed calculation",
            },
            "som": {
                "value": "$1M - $10M",
                "description": "Realistic 3-year target",
                "calculation": "Requires AI for detailed calculation",
            },
            "market_growth_rate": "10-15% (industry average)",
            "key_assumptions": ["Market data requires AI analysis"],
            "comparable_companies": [],
            "confidence_level": "low",
            "data_sources": ["Estimation based on sector averages"],
        }

    async def generate_validation_plan(self, opportunity: dict) -> dict:
        """Local rule-based validation plan."""
        return {
            "validation_goal": "Validate core value proposition",
            "hypothesis": "Users will pay for a solution to this problem",
            "success_criteria": "10+ signups, 3+ interviews with positive feedback",
            "hour_by_hour_plan": [
                {
                    "hours": "0-4",
                    "task": "Create landing page",
                    "deliverable": "Live landing page",
                },
                {
                    "hours": "4-8",
                    "task": "Write copy and design",
                    "deliverable": "Compelling value proposition",
                },
                {
                    "hours": "8-16",
                    "task": "Share on Reddit/Twitter",
                    "deliverable": "Initial traffic",
                },
                {
                    "hours": "16-24",
                    "task": "Collect signups",
                    "deliverable": "Email list",
                },
                {
                    "hours": "24-36",
                    "task": "Reach out for interviews",
                    "deliverable": "Scheduled calls",
                },
                {
                    "hours": "36-48",
                    "task": "Analyze results",
                    "deliverable": "Go/no-go decision",
                },
            ],
            "landing_page": {
                "headline_options": [
                    f"Stop wasting time on {opportunity.get('title', 'this problem')}",
                    f"The simple solution for {opportunity.get('sector', 'your needs')}",
                ],
                "value_propositions": [
                    "Save hours every week",
                    "Simple and affordable",
                    "Built for people like you",
                ],
                "cta_options": ["Get Early Access", "Join Waitlist"],
                "recommended_tool": "Carrd ($19/year)",
            },
            "quick_experiments": [
                {
                    "experiment": "Landing page test",
                    "description": "Create simple page with email capture",
                    "success_metric": "10+ signups",
                    "time_needed": "4 hours",
                },
                {
                    "experiment": "Reddit post",
                    "description": "Share in relevant subreddit",
                    "success_metric": "Positive comments, DMs",
                    "time_needed": "1 hour",
                },
            ],
            "survey_questions": [
                "How do you currently solve this problem?",
                "What's the most frustrating part?",
                "Would you pay $X/month for a solution?",
            ],
            "where_to_find_users": [
                {
                    "platform": "Reddit",
                    "specific_location": "r/Entrepreneur",
                    "approach": "Share as story/question",
                },
                {
                    "platform": "Twitter",
                    "specific_location": "#buildinpublic",
                    "approach": "Share progress",
                },
            ],
            "minimum_validation_signals": {
                "email_signups": "10",
                "survey_responses": "5",
                "positive_feedback_ratio": "70%",
            },
            "go_no_go_decision": "Proceed if 10+ signups AND 3+ positive interviews",
        }

    async def analyze_skill_requirements(self, opportunity: dict) -> dict:
        """Local rule-based skill requirements analysis."""
        product_type = opportunity.get("product_type", "SaaS")
        sector = opportunity.get("sector", "Other")

        # Define skill templates based on product type
        skill_templates = {
            "SaaS": [
                {
                    "skill": "React/Vue",
                    "category": "frontend",
                    "level": "intermediate",
                    "importance": "critical",
                },
                {
                    "skill": "Node.js/Python",
                    "category": "backend",
                    "level": "intermediate",
                    "importance": "critical",
                },
                {
                    "skill": "PostgreSQL",
                    "category": "database",
                    "level": "beginner",
                    "importance": "important",
                },
                {
                    "skill": "REST API Design",
                    "category": "backend",
                    "level": "intermediate",
                    "importance": "critical",
                },
                {
                    "skill": "Authentication",
                    "category": "backend",
                    "level": "intermediate",
                    "importance": "critical",
                },
            ],
            "Mobile App": [
                {
                    "skill": "React Native/Flutter",
                    "category": "frontend",
                    "level": "intermediate",
                    "importance": "critical",
                },
                {
                    "skill": "Mobile UI/UX",
                    "category": "design",
                    "level": "intermediate",
                    "importance": "important",
                },
                {
                    "skill": "App Store Deployment",
                    "category": "devops",
                    "level": "beginner",
                    "importance": "important",
                },
            ],
            "Chrome Extension": [
                {
                    "skill": "JavaScript",
                    "category": "frontend",
                    "level": "intermediate",
                    "importance": "critical",
                },
                {
                    "skill": "Chrome Extension APIs",
                    "category": "frontend",
                    "level": "intermediate",
                    "importance": "critical",
                },
                {
                    "skill": "HTML/CSS",
                    "category": "frontend",
                    "level": "beginner",
                    "importance": "important",
                },
            ],
            "API": [
                {
                    "skill": "Python/Node.js",
                    "category": "backend",
                    "level": "intermediate",
                    "importance": "critical",
                },
                {
                    "skill": "API Design",
                    "category": "backend",
                    "level": "intermediate",
                    "importance": "critical",
                },
                {
                    "skill": "Documentation",
                    "category": "backend",
                    "level": "beginner",
                    "importance": "important",
                },
            ],
            "Telegram Bot": [
                {
                    "skill": "Python",
                    "category": "backend",
                    "level": "beginner",
                    "importance": "critical",
                },
                {
                    "skill": "Telegram Bot API",
                    "category": "backend",
                    "level": "beginner",
                    "importance": "critical",
                },
            ],
            "AI Agent": [
                {
                    "skill": "Python",
                    "category": "backend",
                    "level": "intermediate",
                    "importance": "critical",
                },
                {
                    "skill": "LLM APIs (OpenAI/Anthropic)",
                    "category": "backend",
                    "level": "intermediate",
                    "importance": "critical",
                },
                {
                    "skill": "Prompt Engineering",
                    "category": "backend",
                    "level": "intermediate",
                    "importance": "critical",
                },
            ],
        }

        required_skills = skill_templates.get(product_type, skill_templates["SaaS"])

        return {
            "required_skills": required_skills,
            "recommended_stack": {
                "frontend": {
                    "tech": "React + TypeScript",
                    "reason": "Most popular, large ecosystem",
                },
                "backend": {
                    "tech": "FastAPI / Node.js",
                    "reason": "Fast development, good performance",
                },
                "database": {"tech": "PostgreSQL", "reason": "Reliable, feature-rich"},
                "hosting": {
                    "tech": "Railway / Vercel",
                    "reason": "Easy deployment, free tier",
                },
                "additional_services": [
                    {"service": "Stripe", "purpose": "Payments"},
                    {"service": "Resend", "purpose": "Transactional emails"},
                ],
            },
            "solo_friendly": {
                "verdict": product_type in ["Chrome Extension", "Telegram Bot", "API"],
                "score": 7
                if product_type in ["Chrome Extension", "Telegram Bot"]
                else 5,
                "reasoning": "Complexity depends on product type and features",
                "bottlenecks": [
                    "Marketing",
                    "Customer support",
                    "Feature prioritization",
                ],
            },
            "mvp_complexity": {
                "level": "medium",
                "estimated_hours": {"beginner": 200, "intermediate": 80, "expert": 40},
                "complexity_factors": [
                    "Authentication",
                    "Payment integration",
                    "Core feature set",
                ],
            },
            "nocode_alternative": {
                "possible": product_type in ["SaaS", "Mobile App"],
                "recommended_tools": ["Bubble", "Webflow + Memberstack", "Glide"],
                "limitations": [
                    "Limited customization",
                    "Performance constraints",
                    "Vendor lock-in",
                ],
                "time_savings": "50-70% faster initial development",
            },
            "learning_path": [
                {
                    "skill": "Core programming",
                    "priority": 1,
                    "resources": ["freeCodeCamp", "The Odin Project"],
                    "time_days": 30,
                },
                {
                    "skill": "Framework basics",
                    "priority": 2,
                    "resources": ["Official docs", "YouTube tutorials"],
                    "time_days": 14,
                },
                {
                    "skill": "Database fundamentals",
                    "priority": 3,
                    "resources": ["SQLBolt", "PostgreSQL Tutorial"],
                    "time_days": 7,
                },
            ],
            "team_recommendation": {
                "min_team_size": 1,
                "ideal_team_size": 2,
                "roles_needed": ["Full-stack developer", "Designer (part-time)"],
                "can_outsource": [
                    "Logo design",
                    "Landing page copy",
                    "Initial marketing",
                ],
            },
            "risk_assessment": {
                "technical_risks": ["Scope creep", "Third-party API dependencies"],
                "skill_gaps": ["Detailed analysis requires AI model"],
                "mitigation_strategies": [
                    "Start with MVP",
                    "Use proven tech stack",
                    "Get early feedback",
                ],
            },
        }


# Shared prompts mixin for API-based clients
class AIAnalysisMixin:
    """Mixin providing shared AI analysis methods using complete_json."""

    async def analyze_opportunity(self, content: str, source: str = "unknown") -> dict:
        """Smart opportunity analysis using LLM."""
        prompt = f"""Analyze this content from {source} and extract business opportunity information.

CONTENT:
{content[:4000]}

Respond with a JSON object containing:
{{
    "is_opportunity": true/false (is this a potential business opportunity?),
    "title": "short descriptive title for the opportunity",
    "summary": "2-3 sentence summary of the opportunity",
    "product_type": "SaaS" | "Mobile App" | "Chrome Extension" | "API" | "Telegram Bot" | "AI Agent" | "Other",
    "sector": "Fintech" | "Health" | "Education" | "Productivity" | "E-commerce" | "Marketing" | "HR" | "Developer Tools" | "Entertainment" | "Other",
    "business_model": "Subscription" | "Freemium" | "One-time" | "Transaction fee" | "Advertising",
    "demand_score": 1-10 (how strong is the demand signal?),
    "market_score": 1-10 (how big is the market potential?),
    "feasibility_score": 1-10 (how feasible for a solo developer?),
    "revenue_score": 1-10 (how clear is the monetization path?),
    "confidence": 0.0-1.0 (how confident are you in this analysis?),
    "competitors": ["list", "of", "known", "competitors"],
    "key_features": ["feature1", "feature2", "feature3"],
    "why_opportunity": "one sentence explaining why this is an opportunity"
}}

Be realistic and critical. Not everything is a good opportunity."""

        result = await self.complete_json(prompt)

        # Calculate total score
        if "demand_score" in result:
            scores = [
                result.get("demand_score", 5) * 1.5,
                result.get("market_score", 5),
                result.get("feasibility_score", 5) * 1.5,
                result.get("revenue_score", 5),
            ]
            result["total_score"] = round(sum(scores) / 5, 2)

        return result

    async def deep_analysis(self, content: str, title: str) -> dict:
        """Deep analysis for when user clicks 'Start Working'."""
        prompt = f"""You are a business analyst. Do a deep analysis of this business opportunity.

TITLE: {title}

CONTENT:
{content[:6000]}

Provide a detailed JSON response:
{{
    "market_analysis": {{
        "target_audience": "who would use this?",
        "market_size": "estimated market size and growth",
        "trends": ["relevant trends"]
    }},
    "competitors": [
        {{"name": "competitor name", "url": "website if known", "strengths": "what they do well", "weaknesses": "where they fail"}}
    ],
    "suggested_features": [
        {{"feature": "feature name", "priority": "high/medium/low", "description": "what it does", "effort": "days to build"}}
    ],
    "go_to_market": {{
        "strategy": "overall approach",
        "channels": ["marketing channels"],
        "first_steps": ["step1", "step2", "step3"]
    }},
    "risks": ["risk1", "risk2"],
    "turkey_fit": "how suitable is this for Turkish market?"
}}"""

        return await self.complete_json(prompt)

    async def analyze_comment_sentiment(self, comment: str) -> dict:
        """Analyze comment sentiment - detect complaints, suggestions, praise."""
        prompt = f"""Analyze this user comment and extract sentiment information.

COMMENT:
{comment[:2000]}

Respond with JSON:
{{
    "sentiment": "complaint" | "suggestion" | "praise" | "question" | "neutral",
    "pain_level": 1-10 (how frustrated is the user?),
    "willingness_to_pay": 1-10 (would they pay for a solution?),
    "urgency": 1-10 (how urgent is their need?),
    "key_problem": "one sentence describing their main problem",
    "desired_solution": "what they actually want"
}}"""

        return await self.complete_json(prompt)

    async def compare_competitors(self, opportunity: str, competitors: list) -> dict:
        """Compare competitors for a given opportunity."""
        prompt = f"""Analyze this business opportunity and compare it with existing competitors.

OPPORTUNITY:
{opportunity[:2000]}

KNOWN COMPETITORS:
{", ".join(competitors[:10])}

Provide a detailed JSON response:
{{
    "swot": {{
        "strengths": ["potential strengths of a new entrant"],
        "weaknesses": ["potential weaknesses"],
        "opportunities": ["market opportunities"],
        "threats": ["competitive threats"]
    }},
    "competitor_analysis": [
        {{"name": "competitor", "pricing": "their pricing model", "gap": "what they're missing"}}
    ],
    "differentiation_strategies": ["strategy1", "strategy2", "strategy3"],
    "recommended_positioning": "how to position against competitors"
}}"""

        return await self.complete_json(prompt)

    async def define_mvp(self, opportunity: dict) -> dict:
        """Define MVP for an opportunity."""
        prompt = f"""Based on this opportunity analysis, define an MVP (Minimum Viable Product).

OPPORTUNITY:
{json.dumps(opportunity, indent=2)[:3000]}

Respond with JSON:
{{
    "mvp_name": "suggested product name",
    "core_features": [
        {{"feature": "name", "description": "what it does", "priority": 1-5, "effort_days": estimated days}}
    ],
    "total_effort_days": total days to build MVP,
    "tech_stack": {{
        "frontend": "recommended frontend",
        "backend": "recommended backend",
        "database": "recommended database",
        "hosting": "recommended hosting"
    }},
    "launch_checklist": ["step1", "step2", "step3"],
    "success_metrics": ["metric1", "metric2"]
}}"""

        return await self.complete_json(prompt)

    async def analyze_trend(self, posts: list) -> dict:
        """Analyze trends from a list of posts."""
        posts_text = "\n---\n".join(
            [p.get("title", "") + ": " + p.get("content", "")[:200] for p in posts[:20]]
        )

        prompt = f"""Analyze these posts to identify trends and patterns.

POSTS:
{posts_text[:4000]}

Respond with JSON:
{{
    "main_theme": "overall theme of these posts",
    "sub_themes": ["theme1", "theme2", "theme3"],
    "trend_direction": "growing" | "stable" | "declining",
    "trend_strength": 1-10,
    "seasonality": "is this seasonal? explain",
    "predicted_growth": "short term prediction",
    "opportunity_summary": "what opportunity does this trend present?"
}}"""

        return await self.complete_json(prompt)

    async def calculate_market_size(self, opportunity: dict) -> dict:
        """Calculate TAM/SAM/SOM for an opportunity."""
        prompt = f"""You are a market research analyst. Calculate the market size for this opportunity.

OPPORTUNITY:
{json.dumps(opportunity, indent=2)[:3000]}

Provide a detailed JSON response with realistic estimates:
{{
    "tam": {{
        "value": "Total Addressable Market in USD (e.g., $50B)",
        "description": "Everyone who could potentially use this product globally",
        "calculation": "How you arrived at this number"
    }},
    "sam": {{
        "value": "Serviceable Addressable Market in USD (e.g., $5B)",
        "description": "The portion of TAM you can realistically target",
        "calculation": "How you arrived at this number"
    }},
    "som": {{
        "value": "Serviceable Obtainable Market in USD (e.g., $50M)",
        "description": "Realistic market share you can capture in 1-3 years",
        "calculation": "How you arrived at this number"
    }},
    "market_growth_rate": "Annual growth rate percentage",
    "key_assumptions": ["assumption1", "assumption2"],
    "comparable_companies": [
        {{"name": "company", "valuation": "their valuation/revenue", "market_share": "estimated share"}}
    ],
    "confidence_level": "low/medium/high",
    "data_sources": ["source1", "source2"]
}}

Be realistic and conservative. Use available market data and comparable companies."""

        return await self.complete_json(prompt)

    async def generate_validation_plan(self, opportunity: dict) -> dict:
        """Generate 48-hour MVP validation plan with experiments."""
        prompt = f"""You are a lean startup expert. Create a 48-hour validation plan for this opportunity.

OPPORTUNITY:
{json.dumps(opportunity, indent=2)[:3000]}

Provide a detailed JSON response:
{{
    "validation_goal": "What we're trying to validate in 48 hours",
    "hypothesis": "The core assumption we need to test",
    "success_criteria": "How we'll know if validation is successful",

    "hour_by_hour_plan": [
        {{"hours": "0-4", "task": "task description", "deliverable": "what you'll have"}},
        {{"hours": "4-8", "task": "task description", "deliverable": "what you'll have"}},
        {{"hours": "8-16", "task": "task description", "deliverable": "what you'll have"}},
        {{"hours": "16-24", "task": "task description", "deliverable": "what you'll have"}},
        {{"hours": "24-36", "task": "task description", "deliverable": "what you'll have"}},
        {{"hours": "36-48", "task": "task description", "deliverable": "what you'll have"}}
    ],

    "landing_page": {{
        "headline_options": ["option1", "option2", "option3"],
        "value_propositions": ["vp1", "vp2", "vp3"],
        "cta_options": ["cta1", "cta2"],
        "recommended_tool": "Carrd/Webflow/etc"
    }},

    "quick_experiments": [
        {{
            "experiment": "name",
            "description": "what to do",
            "success_metric": "how to measure",
            "time_needed": "hours"
        }}
    ],

    "survey_questions": [
        "question1?",
        "question2?",
        "question3?"
    ],

    "where_to_find_users": [
        {{"platform": "Reddit/Twitter/etc", "specific_location": "subreddit/hashtag", "approach": "how to engage"}}
    ],

    "minimum_validation_signals": {{
        "email_signups": "target number",
        "survey_responses": "target number",
        "positive_feedback_ratio": "target percentage"
    }},

    "go_no_go_decision": "Clear criteria for deciding to proceed or pivot"
}}

Focus on speed and actionable steps. No coding required in first 48 hours."""

        return await self.complete_json(prompt)

    async def analyze_skill_requirements(self, opportunity: dict) -> dict:
        """Analyze required skills and technologies to build this opportunity."""
        prompt = f"""You are a senior technical architect. Analyze the skills and technologies needed to build this product.

OPPORTUNITY:
{json.dumps(opportunity, indent=2)[:3000]}

Provide a detailed JSON response:
{{
    "required_skills": [
        {{
            "skill": "skill name",
            "category": "frontend" | "backend" | "database" | "devops" | "design" | "marketing" | "domain",
            "level": "beginner" | "intermediate" | "advanced",
            "importance": "critical" | "important" | "nice_to_have",
            "learning_time_days": estimated days to learn from scratch
        }}
    ],

    "recommended_stack": {{
        "frontend": {{"tech": "React/Vue/etc", "reason": "why this choice"}},
        "backend": {{"tech": "Python/Node/etc", "reason": "why this choice"}},
        "database": {{"tech": "PostgreSQL/MongoDB/etc", "reason": "why this choice"}},
        "hosting": {{"tech": "Vercel/Railway/etc", "reason": "why this choice"}},
        "additional_services": [{{"service": "Stripe/Auth0/etc", "purpose": "what it does"}}]
    }},

    "solo_friendly": {{
        "verdict": true/false,
        "score": 1-10 (how suitable for a solo developer),
        "reasoning": "explain why",
        "bottlenecks": ["potential solo dev challenges"]
    }},

    "mvp_complexity": {{
        "level": "low" | "medium" | "high",
        "estimated_hours": {{
            "beginner": hours for beginner,
            "intermediate": hours for intermediate dev,
            "expert": hours for expert
        }},
        "complexity_factors": ["what makes it complex or simple"]
    }},

    "nocode_alternative": {{
        "possible": true/false,
        "recommended_tools": ["Bubble", "Webflow", etc],
        "limitations": ["what you can't do with no-code"],
        "time_savings": "percentage faster than coding"
    }},

    "learning_path": [
        {{
            "skill": "skill to learn",
            "priority": 1-5 (1 = learn first),
            "resources": ["recommended learning resources"],
            "time_days": estimated days
        }}
    ],

    "team_recommendation": {{
        "min_team_size": 1-5,
        "ideal_team_size": 1-5,
        "roles_needed": ["role1", "role2"],
        "can_outsource": ["tasks that can be outsourced"]
    }},

    "risk_assessment": {{
        "technical_risks": ["risk1", "risk2"],
        "skill_gaps": ["most challenging skill areas"],
        "mitigation_strategies": ["how to reduce risks"]
    }}
}}

Be realistic about skill requirements. Consider both building AND maintaining the product."""

        return await self.complete_json(prompt)


class GeminiClient(AIAnalysisMixin, BaseAIClient):
    """Google Gemini API client with fallback to local analysis."""

    def __init__(self):
        self.api_key = settings.gemini_api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.model = "gemini-2.0-flash"
        self.fallback = LocalAnalyzer()

    async def complete(self, prompt: str, system: str | None = None) -> str:
        """Generate completion with fallback."""
        try:
            return await self._api_complete(prompt, system)
        except Exception as e:
            logger.warning(f"API error, using local analysis: {e}")
            return await self.fallback.complete(prompt, system)

    async def _api_complete(self, prompt: str, system: str | None = None) -> str:
        full_prompt = prompt
        if system:
            full_prompt = f"{system}\n\n{prompt}"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/models/{self.model}:generateContent",
                params={"key": self.api_key},
                json={
                    "contents": [{"parts": [{"text": full_prompt}]}],
                    "generationConfig": {"temperature": 0.7, "maxOutputTokens": 4096},
                },
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "")
            return ""

    async def complete_json(self, prompt: str, system: str | None = None) -> dict:
        """Generate JSON with fallback."""
        try:
            json_system = (system or "") + "\n\nRespond with valid JSON only."
            response = await self._api_complete(prompt, json_system)
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            return json.loads(response.strip())
        except Exception as e:
            logger.warning(f"API JSON error, using local analysis: {e}")
            return await self.fallback.complete_json(prompt, system)


class ClaudeClient(AIAnalysisMixin, BaseAIClient):
    """Claude API client with fallback."""

    def __init__(self):
        self.api_key = settings.claude_api_key
        self.base_url = settings.claude_base_url or "https://api.anthropic.com"
        self.fallback = LocalAnalyzer()

    async def complete(self, prompt: str, system: str | None = None) -> str:
        try:
            return await self._api_complete(prompt, system)
        except Exception as e:
            logger.warning(f"API error, using local analysis: {e}")
            return await self.fallback.complete(prompt, system)

    async def _api_complete(self, prompt: str, system: str | None = None) -> str:
        async with httpx.AsyncClient() as client:
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }
            payload = {
                "model": "claude-3-haiku-20240307",
                "max_tokens": 4096,
                "messages": [{"role": "user", "content": prompt}],
            }
            if system:
                payload["system"] = system

            response = await client.post(
                f"{self.base_url}/v1/messages",
                headers=headers,
                json=payload,
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]

    async def complete_json(self, prompt: str, system: str | None = None) -> dict:
        try:
            json_system = (system or "") + "\n\nRespond with valid JSON only."
            response = await self._api_complete(prompt, json_system)
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            return json.loads(response.strip())
        except Exception as e:
            logger.warning(f"API JSON error, using local analysis: {e}")
            return await self.fallback.complete_json(prompt, system)


def get_ai_client() -> BaseAIClient:
    """Get the configured AI client.

    Priority: openrouter -> gemini -> claude -> ollama -> local
    """
    provider = settings.ai_provider

    if provider == "openrouter":
        if settings.openrouter_api_key:
            return OpenRouterClient()
        logger.warning("OpenRouter API key not set, trying Gemini...")
        provider = "gemini"

    if provider == "gemini":
        if settings.gemini_api_key:
            return GeminiClient()
        logger.warning("Gemini API key not set, trying Claude...")
        provider = "claude"

    if provider == "claude":
        if settings.claude_api_key:
            return ClaudeClient()
        logger.warning("Claude API key not set, trying Ollama...")
        provider = "ollama"

    if provider == "ollama" or provider == "local":
        return OllamaClient()

    # Default to Ollama
    return OllamaClient()
