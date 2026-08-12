"""
fetcher.py — pulls jobs from Adzuna (India) and Remotive (remote).
All functions are async and return a list of normalised job dicts.
"""

import asyncio
import hashlib
import logging
from datetime import datetime, timezone

import httpx

from config import (
    ADZUNA_APP_ID, ADZUNA_APP_KEY, ADZUNA_BASE, ADZUNA_QUERIES,
    REMOTIVE_BASE,
)

logger = logging.getLogger(__name__)

# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_id(*parts: str) -> str:
    return hashlib.md5("|".join(parts).encode()).hexdigest()

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Adzuna ────────────────────────────────────────────────────────────────────

async def fetch_adzuna(client: httpx.AsyncClient, query: str, page: int = 1) -> list[dict]:
    """Fetch one page of Adzuna results for a query."""
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        logger.warning("Adzuna credentials not set — skipping")
        return []

    params = {
        "app_id":       ADZUNA_APP_ID,
        "app_key":      ADZUNA_APP_KEY,
        "results_per_page": 50,
        "what":         query,
        "where":        "india",        # India-wide
        "content-type": "application/json",
    }
    try:
        resp = await client.get(f"{ADZUNA_BASE}/{page}", params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        results = []
        for item in data.get("results", []):
            job = {
                "id":          _make_id("adzuna", str(item.get("id", "")), item.get("title", "")),
                "title":       str(item.get("title") or "").strip(),
                "company":     str((item.get("company") or {}).get("display_name") or "Unknown"),
                "location":    _adzuna_location(item),
                "description": str(item.get("description") or ""),
                "url":         str(item.get("redirect_url") or ""),
                "salary":      _adzuna_salary(item),
                "source":      "Adzuna",
                "posted_at":   str(item.get("created") or _now_iso()),
                "fetched_at":  _now_iso(),
            }
            if job["url"] and job["title"]:
                results.append(job)
        return results
    except Exception as e:
        logger.error(f"Adzuna fetch error for '{query}': {e}")
        return []


def _adzuna_location(item: dict) -> str:
    """Safely extract location string — area field can be mixed list."""
    loc = item.get("location") or {}
    display = loc.get("display_name")
    if display:
        return str(display)
    area = loc.get("area") or []
    parts = [str(p) for p in area if p]
    return ", ".join(parts) if parts else "India"


def _adzuna_salary(item: dict) -> str:
    lo = item.get("salary_min")
    hi = item.get("salary_max")
    if lo and hi:
        return f"₹{int(lo):,} – ₹{int(hi):,}"
    if lo:
        return f"₹{int(lo):,}+"
    return ""


async def fetch_all_adzuna(client: httpx.AsyncClient) -> list[dict]:
    """Run Adzuna queries in small batches with delays to avoid 429."""
    jobs: list[dict] = []
    seen_urls: set[str] = set()
    batch_size = 3   # max concurrent requests
    delay_secs = 1.0 # delay between batches

    for i in range(0, len(ADZUNA_QUERIES), batch_size):
        batch_queries = ADZUNA_QUERIES[i:i + batch_size]
        tasks = [fetch_adzuna(client, q) for q in batch_queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for batch in results:
            if isinstance(batch, Exception):
                logger.warning(f"Batch gather exception: {batch}")
                continue
            for job in batch:
                if job["url"] not in seen_urls:
                    seen_urls.add(job["url"])
                    jobs.append(job)
        if i + batch_size < len(ADZUNA_QUERIES):
            await asyncio.sleep(delay_secs)
    return jobs


# ── Remotive ──────────────────────────────────────────────────────────────────

async def fetch_remotive(client: httpx.AsyncClient) -> list[dict]:
    """Fetch remote ECE-relevant jobs from Remotive (no key needed)."""
    all_jobs: list[dict] = []
    seen_urls: set[str] = set()

    # Search by tag keywords
    search_terms = [
        "embedded", "firmware", "hardware", "iot", "electronics",
        "fpga", "robotics", "microcontroller",
    ]
    for term in search_terms:
        try:
            resp = await client.get(
                REMOTIVE_BASE,
                params={"search": term, "limit": 50},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            for item in data.get("jobs", []):
                url = item.get("url", "")
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                job = {
                    "id":          _make_id("remotive", str(item.get("id", "")), url),
                    "title":       item.get("title", "").strip(),
                    "company":     item.get("company_name", "Unknown"),
                    "location":    item.get("candidate_required_location") or "Remote",
                    "description": item.get("description", ""),
                    "url":         url,
                    "salary":      item.get("salary", ""),
                    "source":      "Remotive",
                    "posted_at":   item.get("publication_date", _now_iso()),
                    "fetched_at":  _now_iso(),
                }
                all_jobs.append(job)
        except Exception as e:
            logger.error(f"Remotive fetch error for '{term}': {e}")

    return all_jobs


# ── Main entry point ──────────────────────────────────────────────────────────

async def fetch_all_jobs() -> list[dict]:
    """Fetch from all sources and return raw normalised job list."""
    async with httpx.AsyncClient(
        headers={"User-Agent": "AtifJobs/1.0 (personal job board)"},
        follow_redirects=True,
    ) as client:
        adzuna_jobs, remotive_jobs = await asyncio.gather(
            fetch_all_adzuna(client),
            fetch_remotive(client),
        )

    all_jobs = adzuna_jobs + remotive_jobs
    logger.info(f"Fetched {len(adzuna_jobs)} Adzuna + {len(remotive_jobs)} Remotive = {len(all_jobs)} total raw jobs")
    return all_jobs
