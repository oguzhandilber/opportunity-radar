"""Tests for export and dashboard endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


class TestDashboardStats:
    """Tests for dashboard stats endpoint with data."""

    def test_get_stats_with_opportunities(self):
        """Test dashboard stats with opportunities in database."""
        from app.main import app

        with TestClient(app) as client:
            response = client.get("/api/dashboard/stats")
            assert response.status_code == 200

            data = response.json()
            # Check all required fields exist
            assert "total_opportunities" in data
            assert "new_opportunities" in data
            assert "saved_opportunities" in data
            assert "total_posts_scraped" in data
            assert "average_score" in data
            assert "top_sectors" in data
            assert "top_product_types" in data

    def test_get_stats_returns_correct_types(self):
        """Test dashboard stats returns correct data types."""
        from app.main import app

        with TestClient(app) as client:
            response = client.get("/api/dashboard/stats")
            data = response.json()

            assert isinstance(data["total_opportunities"], int)
            assert isinstance(data["new_opportunities"], int)
            assert isinstance(data["saved_opportunities"], int)
            assert isinstance(data["total_posts_scraped"], int)
            assert isinstance(data["average_score"], (int, float))
            assert isinstance(data["top_sectors"], list)
            assert isinstance(data["top_product_types"], list)


class TestExportCSV:
    """Tests for CSV export endpoint."""

    def test_export_csv_empty(self):
        """Test CSV export with no data."""
        from app.main import app

        with TestClient(app) as client:
            response = client.get("/api/export/csv")
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/csv; charset=utf-8"
            assert "attachment" in response.headers.get("content-disposition", "")

    def test_export_csv_has_headers(self):
        """Test CSV export has proper headers."""
        from app.main import app

        with TestClient(app) as client:
            response = client.get("/api/export/csv")
            content = response.content.decode("utf-8")

            # Check for expected CSV headers
            assert "ID" in content
            assert "Title" in content
            assert "Summary" in content
            assert "Product Type" in content
            assert "Total Score" in content

    def test_export_csv_with_status_filter(self):
        """Test CSV export with status filter."""
        from app.main import app

        with TestClient(app) as client:
            response = client.get("/api/export/csv?status=new")
            assert response.status_code == 200

    def test_export_csv_with_min_score_filter(self):
        """Test CSV export with min_score filter."""
        from app.main import app

        with TestClient(app) as client:
            response = client.get("/api/export/csv?min_score=5.0")
            assert response.status_code == 200

    def test_export_csv_with_invalid_min_score(self):
        """Test CSV export rejects invalid min_score."""
        from app.main import app

        with TestClient(app) as client:
            response = client.get("/api/export/csv?min_score=15")
            assert response.status_code == 422  # Validation error

    def test_export_csv_with_combined_filters(self):
        """Test CSV export with multiple filters."""
        from app.main import app

        with TestClient(app) as client:
            response = client.get("/api/export/csv?status=saved&min_score=7.0")
            assert response.status_code == 200


class TestExportJSON:
    """Tests for JSON export endpoint."""

    def test_export_json_empty(self):
        """Test JSON export with no data."""
        from app.main import app

        with TestClient(app) as client:
            response = client.get("/api/export/json")
            assert response.status_code == 200
            assert "application/json" in response.headers["content-type"]
            assert "attachment" in response.headers.get("content-disposition", "")

    def test_export_json_returns_array(self):
        """Test JSON export returns array."""
        from app.main import app

        with TestClient(app) as client:
            response = client.get("/api/export/json")
            content = response.content.decode("utf-8")
            import json
            data = json.loads(content)
            assert isinstance(data, list)

    def test_export_json_with_status_filter(self):
        """Test JSON export with status filter."""
        from app.main import app

        with TestClient(app) as client:
            response = client.get("/api/export/json?status=new")
            assert response.status_code == 200

    def test_export_json_with_min_score_filter(self):
        """Test JSON export with min_score filter."""
        from app.main import app

        with TestClient(app) as client:
            response = client.get("/api/export/json?min_score=8.0")
            assert response.status_code == 200

    def test_export_json_min_score_validation(self):
        """Test JSON export validates min_score range."""
        from app.main import app

        with TestClient(app) as client:
            # Too high
            response = client.get("/api/export/json?min_score=11")
            assert response.status_code == 422

            # Too low (negative)
            response = client.get("/api/export/json?min_score=-1")
            assert response.status_code == 422

    def test_export_json_with_combined_filters(self):
        """Test JSON export with combined filters."""
        from app.main import app

        with TestClient(app) as client:
            response = client.get("/api/export/json?status=working&min_score=6.5")
            assert response.status_code == 200


class TestScrapeAPI:
    """Tests for scrape API endpoints."""

    def test_scrape_status_endpoint(self):
        """Test scrape status endpoint."""
        from app.main import app

        with TestClient(app) as client:
            response = client.get("/api/scrape/status")
            assert response.status_code == 200

            data = response.json()
            assert "is_running" in data
            assert "last_run" in data
            assert "last_result" in data

    def test_trigger_scrape_starts_job(self):
        """Test trigger scrape starts background job."""
        from app.main import app
        from app.api.scrape import scrape_status

        # Reset status first
        scrape_status["is_running"] = False
        scrape_status["last_run"] = None

        with TestClient(app) as client:
            # Mock the background task to prevent actual execution
            with patch("app.api.scrape.run_scrape_job"):
                response = client.post("/api/scrape/trigger")
                assert response.status_code == 200

                data = response.json()
                assert "message" in data
                assert "started" in data["message"].lower() or "running" in data["message"].lower()

    def test_trigger_scrape_when_already_running(self):
        """Test trigger scrape when job already running."""
        from app.main import app
        from app.api.scrape import scrape_status

        scrape_status["is_running"] = True

        with TestClient(app) as client:
            response = client.post("/api/scrape/trigger")
            assert response.status_code == 200

            data = response.json()
            assert "already running" in data["message"].lower()

            # Reset
            scrape_status["is_running"] = False
