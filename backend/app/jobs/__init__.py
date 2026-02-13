"""Job queue initialization.

NOTE: This module is currently NOT IN USE.
=====================================
The Redis/RQ job queue infrastructure is implemented but not integrated
into the main application flow. It's kept for future use when background
job processing becomes necessary.

To enable:
1. Install Redis and ensure it's running
2. Set REDIS_URL in .env
3. Start an RQ worker: rq worker -u $REDIS_URL
4. Import and use enqueue_job() from this module
"""

from app.jobs.queue import get_queue, enqueue_job
from app.jobs.tasks import scrape_all_sources, analyze_opportunity

__all__ = ["get_queue", "enqueue_job", "scrape_all_sources", "analyze_opportunity"]
