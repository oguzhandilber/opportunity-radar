"""Scraping API endpoints."""

from fastapi import APIRouter, BackgroundTasks, Request

from app.middleware.rate_limit import limiter

router = APIRouter()

# Track scraping status
scrape_status = {
    "is_running": False,
    "last_run": None,
    "last_result": None,
}


async def run_scrape_job():
    """Run the full scraping and analysis pipeline."""
    from datetime import datetime, timezone

    from app.analyzers.pipeline import run_analysis_pipeline
    from app.scrapers.manager import run_all_scrapers

    global scrape_status
    scrape_status["is_running"] = True

    try:
        # Run all scrapers
        scrape_results = await run_all_scrapers()

        # Run analysis pipeline on new posts
        analysis_results = await run_analysis_pipeline()

        scrape_status["last_result"] = {
            "posts_scraped": scrape_results.get("total_posts", 0),
            "opportunities_found": analysis_results.get("opportunities_created", 0),
            "errors": scrape_results.get("errors", [])
            + analysis_results.get("errors", []),
        }
    except Exception as e:
        scrape_status["last_result"] = {"error": str(e)}
    finally:
        scrape_status["is_running"] = False
        scrape_status["last_run"] = datetime.now(timezone.utc).isoformat()


@router.post("/trigger")
@limiter.limit("5/minute")
async def trigger_scrape(request: Request, background_tasks: BackgroundTasks):
    """Trigger a manual scrape job."""
    if scrape_status["is_running"]:
        return {"message": "Scrape job already running", "status": scrape_status}

    background_tasks.add_task(run_scrape_job)
    return {"message": "Scrape job started", "status": "running"}


@router.get("/status")
async def get_scrape_status():
    """Get the current scraping status."""
    return scrape_status
