"""
main.py — FastAPI application entry point.
Serves the REST API and the static frontend from /static.
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from jobs_db import init_db, get_jobs, get_stats, toggle_saved
from scheduler import start_scheduler, stop_scheduler, run_refresh

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: init DB, start scheduler, run first fetch immediately."""
    init_db()
    start_scheduler()
    logger.info("🚀 AtifJobs starting — running initial job fetch …")
    await run_refresh()         # immediate first load
    yield
    stop_scheduler()
    logger.info("👋 AtifJobs shutting down")


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="AtifJobs API",
    description="Personal ECE job board for Mohammed Atif",
    version="1.0.0",
    lifespan=lifespan,
)


# ── API Routes ────────────────────────────────────────────────────────────────

@app.get("/api/jobs")
async def api_jobs(
    category: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    source:   Optional[str] = Query(None),
    sort:     str           = Query("match_score"),
    min_score: int          = Query(25),
    limit:    int           = Query(200),
):
    jobs = get_jobs(
        category=category,
        location=location,
        source=source,
        min_score=min_score,
        sort_by=sort,
        limit=limit,
    )
    return {"jobs": jobs, "count": len(jobs)}


@app.get("/api/stats")
async def api_stats():
    return get_stats()


@app.post("/api/refresh")
async def api_refresh():
    """Manually trigger a job refresh (useful for testing)."""
    await run_refresh()
    return {"status": "ok", "message": "Refresh complete"}


@app.post("/api/jobs/{job_id}/save")
async def api_save(job_id: str, saved: bool = Query(True)):
    toggle_saved(job_id, saved)
    return {"status": "ok"}


@app.get("/api/health")
async def health():
    return {"status": "healthy"}


# ── Static frontend ───────────────────────────────────────────────────────────

static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def root():
    return FileResponse(os.path.join(static_dir, "index.html"))


# ── Dev runner ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
