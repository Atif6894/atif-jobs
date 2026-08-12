"""
scheduler.py — background job that refreshes the job database periodically.
"""

import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import REFRESH_INTERVAL_MINUTES
from fetcher import fetch_all_jobs
from scorer import process_job
from jobs_db import upsert_job, set_meta, delete_old_jobs

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


async def run_refresh():
    """Fetch → score → store all fresh jobs."""
    logger.info("🔄 Job refresh started …")
    try:
        raw_jobs = await fetch_all_jobs()
        saved = 0
        for raw in raw_jobs:
            processed = process_job(raw)
            if processed:
                upsert_job(processed)
                saved += 1

        delete_old_jobs(days=30)
        now = datetime.now(timezone.utc).isoformat()
        set_meta("last_updated", now)
        logger.info(f"✅ Refresh done — {saved}/{len(raw_jobs)} jobs saved to DB")
    except Exception as e:
        logger.error(f"❌ Refresh failed: {e}", exc_info=True)


def start_scheduler():
    global _scheduler
    _scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")
    _scheduler.add_job(
        run_refresh,
        trigger="interval",
        minutes=REFRESH_INTERVAL_MINUTES,
        id="job_refresh",
        replace_existing=True,
        misfire_grace_time=60,
    )
    _scheduler.start()
    logger.info(f"⏰ Scheduler started — refreshing every {REFRESH_INTERVAL_MINUTES} min")


def stop_scheduler():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
