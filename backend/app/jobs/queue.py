"""Redis Queue connection and utilities.

NOTE: NOT CURRENTLY IN USE
==========================
This module provides Redis/RQ job queue infrastructure for background task
processing. It is fully implemented but not yet integrated into the main
application flow.

Future use cases:
- Long-running scraping jobs
- Background AI analysis
- Scheduled tasks

To use:
1. Install Redis (brew install redis / apt install redis-server)
2. Start Redis server
3. Set REDIS_URL in .env (default: redis://localhost:6379/0)
4. Start RQ worker: rq worker -u $REDIS_URL
"""

import logging
from typing import Any, Callable, Optional

from redis import Redis
from rq import Queue
from rq.job import Job

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Redis connection (lazy initialization)
_redis_conn: Optional[Redis] = None
_queue: Optional[Queue] = None


def get_redis() -> Redis:
    """Get Redis connection (lazy initialization)."""
    global _redis_conn
    if _redis_conn is None:
        redis_url = getattr(settings, "redis_url", "redis://localhost:6379/0")
        _redis_conn = Redis.from_url(redis_url)
        logger.info(f"Connected to Redis at {redis_url}")
    return _redis_conn


def get_queue(name: str = "default") -> Queue:
    """Get RQ queue instance."""
    global _queue
    if _queue is None or _queue.name != name:
        _queue = Queue(name, connection=get_redis())
    return _queue


def enqueue_job(
    func: Callable,
    *args,
    queue_name: str = "default",
    job_timeout: int = 600,  # 10 minutes default
    result_ttl: int = 86400,  # 24 hours
    **kwargs
) -> Job:
    """Enqueue a job for background execution.

    Args:
        func: The function to execute
        *args: Positional arguments for the function
        queue_name: Name of the queue (default, high, low)
        job_timeout: Maximum time for job execution in seconds
        result_ttl: How long to keep the result
        **kwargs: Keyword arguments for the function

    Returns:
        The enqueued Job object
    """
    queue = get_queue(queue_name)
    job = queue.enqueue(
        func,
        *args,
        job_timeout=job_timeout,
        result_ttl=result_ttl,
        **kwargs
    )
    logger.info(f"Enqueued job {job.id}: {func.__name__}")
    return job


def get_job_status(job_id: str) -> dict[str, Any]:
    """Get status of a job by ID.

    Returns:
        Dict with job status information
    """
    try:
        job = Job.fetch(job_id, connection=get_redis())
        return {
            "id": job.id,
            "status": job.get_status(),
            "result": job.result,
            "error": job.exc_info,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "ended_at": job.ended_at.isoformat() if job.ended_at else None,
        }
    except Exception as e:
        logger.error(f"Failed to fetch job {job_id}: {e}")
        return {"id": job_id, "status": "not_found", "error": str(e)}


def is_redis_available() -> bool:
    """Check if Redis is available."""
    try:
        redis = get_redis()
        redis.ping()
        return True
    except Exception as e:
        logger.warning(f"Redis not available: {e}")
        return False
