"""Tests for analysis pipeline."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestAnalysisPipeline:
    """Tests for run_analysis_pipeline function."""

    @pytest.mark.asyncio
    async def test_run_analysis_pipeline_no_posts(self):
        """Test pipeline with no unprocessed posts."""
        from app.analyzers.pipeline import run_analysis_pipeline

        with patch("app.analyzers.pipeline.get_db_context") as mock_db:
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session.commit = AsyncMock()

            mock_ctx = AsyncMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
            mock_ctx.__aexit__ = AsyncMock(return_value=None)
            mock_db.return_value = mock_ctx

            result = await run_analysis_pipeline()

            assert result["opportunities_created"] == 0
            assert result["skipped"] == 0
            assert result["errors"] == []

    @pytest.mark.asyncio
    async def test_run_analysis_pipeline_filters_irrelevant(self):
        """Test pipeline filters irrelevant content."""
        from app.analyzers.pipeline import run_analysis_pipeline

        with patch("app.analyzers.pipeline.get_db_context") as mock_db, \
             patch("app.analyzers.pipeline.ContentFilter") as mock_filter_class:

            # Setup mock post
            mock_post = MagicMock()
            mock_post.id = 1
            mock_post.content = "Short spam"
            mock_post.source = "test"

            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_post]
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session.commit = AsyncMock()

            mock_ctx = AsyncMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
            mock_ctx.__aexit__ = AsyncMock(return_value=None)
            mock_db.return_value = mock_ctx

            # Filter rejects the content
            mock_filter = MagicMock()
            mock_filter.is_relevant.return_value = False
            mock_filter_class.return_value = mock_filter

            result = await run_analysis_pipeline()

            assert result["skipped"] == 1
            assert result["opportunities_created"] == 0

    @pytest.mark.asyncio
    async def test_run_analysis_pipeline_with_ollama_client(self):
        """Test pipeline with Ollama client."""
        from app.analyzers.pipeline import run_analysis_pipeline
        from app.analyzers.ai_client import OllamaClient

        with patch("app.analyzers.pipeline.get_db_context") as mock_db, \
             patch("app.analyzers.pipeline.ContentFilter") as mock_filter_class, \
             patch("app.analyzers.pipeline.get_ai_client") as mock_get_client:

            # Setup mock post
            mock_post = MagicMock()
            mock_post.id = 1
            mock_post.content = "I wish there was a tool for managing my tasks better"
            mock_post.source = "reddit"

            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_post]
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session.add = MagicMock()
            mock_session.commit = AsyncMock()

            mock_ctx = AsyncMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
            mock_ctx.__aexit__ = AsyncMock(return_value=None)
            mock_db.return_value = mock_ctx

            # Filter passes the content
            mock_filter = MagicMock()
            mock_filter.is_relevant.return_value = True
            mock_filter_class.return_value = mock_filter

            # Mock Ollama client
            mock_ollama = MagicMock(spec=OllamaClient)
            mock_ollama.analyze_opportunity = AsyncMock(return_value={
                "is_opportunity": True,
                "title": "Task Manager",
                "summary": "A tool for managing tasks",
                "product_type": "SaaS",
                "sector": "Productivity",
                "business_model": "Subscription",
                "demand_score": 7,
                "market_score": 6,
                "feasibility_score": 8,
                "revenue_score": 6,
                "total_score": 6.75,
                "confidence": 0.8,
                "competitors": ["Todoist", "Asana"],
                "key_features": ["Task creation", "Reminders"],
            })
            mock_get_client.return_value = mock_ollama

            result = await run_analysis_pipeline()

            assert result["opportunities_created"] == 1
            mock_ollama.analyze_opportunity.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_analysis_pipeline_handles_not_opportunity(self):
        """Test pipeline handles AI returning not an opportunity."""
        from app.analyzers.pipeline import run_analysis_pipeline
        from app.analyzers.ai_client import OllamaClient

        with patch("app.analyzers.pipeline.get_db_context") as mock_db, \
             patch("app.analyzers.pipeline.ContentFilter") as mock_filter_class, \
             patch("app.analyzers.pipeline.get_ai_client") as mock_get_client:

            mock_post = MagicMock()
            mock_post.id = 1
            mock_post.content = "Just a regular post"
            mock_post.source = "reddit"

            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_post]
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session.commit = AsyncMock()

            mock_ctx = AsyncMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
            mock_ctx.__aexit__ = AsyncMock(return_value=None)
            mock_db.return_value = mock_ctx

            mock_filter = MagicMock()
            mock_filter.is_relevant.return_value = True
            mock_filter_class.return_value = mock_filter

            mock_ollama = MagicMock(spec=OllamaClient)
            mock_ollama.analyze_opportunity = AsyncMock(return_value={
                "is_opportunity": False,
            })
            mock_get_client.return_value = mock_ollama

            result = await run_analysis_pipeline()

            assert result["skipped"] == 1
            assert result["opportunities_created"] == 0

    @pytest.mark.asyncio
    async def test_run_analysis_pipeline_handles_error(self):
        """Test pipeline handles errors gracefully."""
        from app.analyzers.pipeline import run_analysis_pipeline
        from app.analyzers.ai_client import OllamaClient

        with patch("app.analyzers.pipeline.get_db_context") as mock_db, \
             patch("app.analyzers.pipeline.ContentFilter") as mock_filter_class, \
             patch("app.analyzers.pipeline.get_ai_client") as mock_get_client:

            mock_post = MagicMock()
            mock_post.id = 1
            mock_post.content = "Test content"
            mock_post.source = "reddit"

            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_post]
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session.commit = AsyncMock()

            mock_ctx = AsyncMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
            mock_ctx.__aexit__ = AsyncMock(return_value=None)
            mock_db.return_value = mock_ctx

            mock_filter = MagicMock()
            mock_filter.is_relevant.return_value = True
            mock_filter_class.return_value = mock_filter

            mock_ollama = MagicMock(spec=OllamaClient)
            mock_ollama.analyze_opportunity = AsyncMock(side_effect=Exception("AI error"))
            mock_get_client.return_value = mock_ollama

            result = await run_analysis_pipeline()

            assert len(result["errors"]) == 1
            assert result["errors"][0]["post_id"] == 1


class TestDeepAnalyzeOpportunity:
    """Tests for deep_analyze_opportunity function."""

    @pytest.mark.asyncio
    async def test_deep_analyze_not_found(self):
        """Test deep analysis with non-existent opportunity."""
        from app.analyzers.pipeline import deep_analyze_opportunity

        with patch("app.analyzers.pipeline.get_db_context") as mock_db:
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_session.execute = AsyncMock(return_value=mock_result)

            mock_ctx = AsyncMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
            mock_ctx.__aexit__ = AsyncMock(return_value=None)
            mock_db.return_value = mock_ctx

            result = await deep_analyze_opportunity(999)

            assert "error" in result
            assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_deep_analyze_with_any_client(self):
        """Test deep analysis works with any AI client."""
        from app.analyzers.pipeline import deep_analyze_opportunity

        with patch("app.analyzers.pipeline.get_db_context") as mock_db, \
             patch("app.analyzers.pipeline.get_ai_client") as mock_get_client:

            # Setup mock opportunity
            mock_opp = MagicMock()
            mock_opp.id = 1
            mock_opp.title = "Test Opportunity"
            mock_opp.summary = "Test summary"
            mock_opp.raw_post_id = 1
            mock_opp.competitors = []
            mock_opp.suggested_features = []
            mock_opp.go_to_market = ""
            mock_opp.notes = ""

            mock_post = MagicMock()
            mock_post.content = "Test content"

            mock_session = AsyncMock()
            mock_opp_result = MagicMock()
            mock_opp_result.scalar_one_or_none.return_value = mock_opp

            mock_post_result = MagicMock()
            mock_post_result.scalar_one_or_none.return_value = mock_post

            mock_session.execute = AsyncMock(side_effect=[mock_opp_result, mock_post_result])
            mock_session.commit = AsyncMock()

            mock_ctx = AsyncMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
            mock_ctx.__aexit__ = AsyncMock(return_value=None)
            mock_db.return_value = mock_ctx

            # Any AI client with async deep_analysis method
            mock_client = MagicMock()
            mock_client.deep_analysis = AsyncMock(return_value={
                "competitors": [{"name": "Rival", "url": "http://rival.com"}],
                "suggested_features": [{"feature": "Dark mode", "priority": "high"}],
                "go_to_market": {"strategy": "ProductHunt launch"},
                "market_analysis": {"target_audience": "Developers"},
            })
            mock_get_client.return_value = mock_client

            result = await deep_analyze_opportunity(1)

            assert result["success"] is True
            assert "analysis" in result
            mock_client.deep_analysis.assert_called_once()

    @pytest.mark.asyncio
    async def test_deep_analyze_with_ollama_success(self):
        """Test deep analysis with Ollama updates opportunity."""
        from app.analyzers.pipeline import deep_analyze_opportunity
        from app.analyzers.ai_client import OllamaClient

        with patch("app.analyzers.pipeline.get_db_context") as mock_db, \
             patch("app.analyzers.pipeline.get_ai_client") as mock_get_client:

            mock_opp = MagicMock()
            mock_opp.id = 1
            mock_opp.title = "Test Opportunity"
            mock_opp.summary = "Test summary"
            mock_opp.raw_post_id = 1
            mock_opp.competitors = []
            mock_opp.suggested_features = []
            mock_opp.go_to_market = ""
            mock_opp.notes = ""

            mock_post = MagicMock()
            mock_post.content = "Test content"

            mock_session = AsyncMock()
            mock_opp_result = MagicMock()
            mock_opp_result.scalar_one_or_none.return_value = mock_opp

            mock_post_result = MagicMock()
            mock_post_result.scalar_one_or_none.return_value = mock_post

            mock_session.execute = AsyncMock(side_effect=[mock_opp_result, mock_post_result])
            mock_session.commit = AsyncMock()

            mock_ctx = AsyncMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
            mock_ctx.__aexit__ = AsyncMock(return_value=None)
            mock_db.return_value = mock_ctx

            mock_ollama = MagicMock(spec=OllamaClient)
            mock_ollama.deep_analysis = AsyncMock(return_value={
                "competitors": [{"name": "Rival", "url": "http://rival.com"}],
                "suggested_features": [{"feature": "Dark mode", "priority": "high"}],
                "go_to_market": "Launch on ProductHunt",
                "market_analysis": {"target_audience": "Developers", "market_size": "$1B"},
                "turkey_fit": "High demand in Istanbul tech scene",
                "risks": ["Competition", "Regulation"],
            })
            mock_get_client.return_value = mock_ollama

            result = await deep_analyze_opportunity(1)

            assert result["success"] is True
            assert "analysis" in result
            mock_ollama.deep_analysis.assert_called_once()
            mock_session.commit.assert_called_once()


class TestAnalyzeOpportunitySkills:
    """Tests for analyze_opportunity_skills function."""

    @pytest.mark.asyncio
    async def test_analyze_skills_not_found(self):
        """Test skill analysis returns error when opportunity not found."""
        from app.analyzers.pipeline import analyze_opportunity_skills

        with patch("app.analyzers.pipeline.get_db_context") as mock_db, \
             patch("app.analyzers.pipeline.get_ai_client") as mock_get_client:

            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_session.execute = AsyncMock(return_value=mock_result)

            mock_ctx = AsyncMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
            mock_ctx.__aexit__ = AsyncMock(return_value=None)
            mock_db.return_value = mock_ctx

            result = await analyze_opportunity_skills(999)

            assert "error" in result
            assert result["error"] == "Opportunity not found"

    @pytest.mark.asyncio
    async def test_analyze_skills_success(self):
        """Test skill analysis returns correct data structure."""
        from app.analyzers.pipeline import analyze_opportunity_skills

        with patch("app.analyzers.pipeline.get_db_context") as mock_db, \
             patch("app.analyzers.pipeline.get_ai_client") as mock_get_client:

            # Setup mock opportunity
            mock_opp = MagicMock()
            mock_opp.id = 1
            mock_opp.title = "Invoice Automation Tool"
            mock_opp.summary = "A tool for automating invoices for freelancers"
            mock_opp.product_type = "SaaS"
            mock_opp.sector = "Fintech"
            mock_opp.business_model = "Subscription"
            mock_opp.demand_score = 8
            mock_opp.market_score = 7
            mock_opp.feasibility_score = 6
            mock_opp.revenue_score = 8
            mock_opp.competitors = ["FreshBooks", "Wave"]
            mock_opp.suggested_features = ["PDF export", "Payment reminders"]

            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_opp
            mock_session.execute = AsyncMock(return_value=mock_result)

            mock_ctx = AsyncMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
            mock_ctx.__aexit__ = AsyncMock(return_value=None)
            mock_db.return_value = mock_ctx

            # Mock AI client response
            mock_client = MagicMock()
            mock_client.analyze_skill_requirements = AsyncMock(return_value={
                "required_skills": [
                    {"skill": "React", "category": "frontend", "level": "intermediate"},
                    {"skill": "Node.js", "category": "backend", "level": "intermediate"},
                ],
                "recommended_stack": {
                    "frontend": {"tech": "React", "reason": "Popular"},
                    "backend": {"tech": "Node.js", "reason": "JavaScript everywhere"},
                },
                "solo_friendly": {"verdict": True, "score": 7},
                "mvp_complexity": {"level": "medium"},
                "nocode_alternative": {"possible": True},
                "learning_path": [{"skill": "React", "priority": 1}],
            })
            mock_get_client.return_value = mock_client

            result = await analyze_opportunity_skills(1)

            assert result["opportunity_id"] == 1
            assert result["title"] == "Invoice Automation Tool"
            assert "skill_analysis" in result
            assert "required_skills" in result["skill_analysis"]
            assert "recommended_stack" in result["skill_analysis"]
            assert "solo_friendly" in result["skill_analysis"]
            mock_client.analyze_skill_requirements.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_skills_with_local_analyzer(self):
        """Test skill analysis works with LocalAnalyzer fallback."""
        from app.analyzers.pipeline import analyze_opportunity_skills
        from app.analyzers.ai_client import LocalAnalyzer

        with patch("app.analyzers.pipeline.get_db_context") as mock_db, \
             patch("app.analyzers.pipeline.get_ai_client") as mock_get_client:

            mock_opp = MagicMock()
            mock_opp.id = 1
            mock_opp.title = "Chrome Extension"
            mock_opp.summary = "Browser extension for productivity"
            mock_opp.product_type = "Chrome Extension"
            mock_opp.sector = "Productivity"
            mock_opp.business_model = "Freemium"
            mock_opp.demand_score = 6
            mock_opp.market_score = 5
            mock_opp.feasibility_score = 8
            mock_opp.revenue_score = 5
            mock_opp.competitors = []
            mock_opp.suggested_features = []

            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_opp
            mock_session.execute = AsyncMock(return_value=mock_result)

            mock_ctx = AsyncMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
            mock_ctx.__aexit__ = AsyncMock(return_value=None)
            mock_db.return_value = mock_ctx

            # Use real LocalAnalyzer
            local_analyzer = LocalAnalyzer()
            mock_get_client.return_value = local_analyzer

            result = await analyze_opportunity_skills(1)

            assert result["opportunity_id"] == 1
            assert "skill_analysis" in result

            skill_analysis = result["skill_analysis"]
            assert "required_skills" in skill_analysis
            assert "recommended_stack" in skill_analysis
            assert "solo_friendly" in skill_analysis
            assert "mvp_complexity" in skill_analysis
            assert "nocode_alternative" in skill_analysis
            assert "learning_path" in skill_analysis

            # Chrome Extension should be solo-friendly
            assert skill_analysis["solo_friendly"]["verdict"] is True


class TestLocalAnalyzerSkillRequirements:
    """Tests for LocalAnalyzer.analyze_skill_requirements."""

    @pytest.mark.asyncio
    async def test_saas_skills(self):
        """Test skill requirements for SaaS product."""
        from app.analyzers.ai_client import LocalAnalyzer

        analyzer = LocalAnalyzer()
        result = await analyzer.analyze_skill_requirements({
            "title": "Project Management SaaS",
            "product_type": "SaaS",
            "sector": "Productivity",
        })

        assert "required_skills" in result
        skills = result["required_skills"]

        # SaaS should require React/Vue and Node.js/Python
        skill_names = [s["skill"] for s in skills]
        assert any("React" in s or "Vue" in s for s in skill_names)
        assert any("Node" in s or "Python" in s for s in skill_names)

    @pytest.mark.asyncio
    async def test_telegram_bot_skills(self):
        """Test skill requirements for Telegram Bot."""
        from app.analyzers.ai_client import LocalAnalyzer

        analyzer = LocalAnalyzer()
        result = await analyzer.analyze_skill_requirements({
            "title": "Trading Bot",
            "product_type": "Telegram Bot",
            "sector": "Fintech",
        })

        assert "required_skills" in result
        skills = result["required_skills"]

        # Telegram bot should be simpler
        skill_names = [s["skill"] for s in skills]
        assert any("Python" in s for s in skill_names)
        assert any("Telegram" in s for s in skill_names)

        # Should be solo-friendly
        assert result["solo_friendly"]["verdict"] is True

    @pytest.mark.asyncio
    async def test_ai_agent_skills(self):
        """Test skill requirements for AI Agent."""
        from app.analyzers.ai_client import LocalAnalyzer

        analyzer = LocalAnalyzer()
        result = await analyzer.analyze_skill_requirements({
            "title": "Customer Support AI",
            "product_type": "AI Agent",
            "sector": "Marketing",
        })

        assert "required_skills" in result
        skills = result["required_skills"]

        # AI Agent should require LLM knowledge
        skill_names = [s["skill"] for s in skills]
        assert any("LLM" in s or "OpenAI" in s or "Anthropic" in s for s in skill_names)
        assert any("Prompt" in s for s in skill_names)

    @pytest.mark.asyncio
    async def test_nocode_alternatives(self):
        """Test no-code alternatives are provided."""
        from app.analyzers.ai_client import LocalAnalyzer

        analyzer = LocalAnalyzer()
        result = await analyzer.analyze_skill_requirements({
            "title": "Landing Page Builder",
            "product_type": "SaaS",
            "sector": "Marketing",
        })

        assert "nocode_alternative" in result
        nocode = result["nocode_alternative"]
        assert "possible" in nocode
        assert "recommended_tools" in nocode
        assert len(nocode["recommended_tools"]) > 0

    @pytest.mark.asyncio
    async def test_learning_path_structure(self):
        """Test learning path has correct structure."""
        from app.analyzers.ai_client import LocalAnalyzer

        analyzer = LocalAnalyzer()
        result = await analyzer.analyze_skill_requirements({
            "title": "E-commerce Platform",
            "product_type": "SaaS",
            "sector": "E-commerce",
        })

        assert "learning_path" in result
        path = result["learning_path"]
        assert len(path) > 0

        for item in path:
            assert "skill" in item
            assert "priority" in item
            assert "resources" in item
            assert "time_days" in item
