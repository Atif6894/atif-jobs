import re
import json
from config import RESUME_KEYWORDS, NEGATIVE_KEYWORDS, JOB_CATEGORIES, MIN_MATCH_SCORE


def _text(job: dict) -> str:
    """Combine title + description into one searchable blob."""
    return (
        (job.get("title") or "") + " " +
        (job.get("description") or "") + " " +
        (job.get("company") or "")
    ).lower()


def is_negative(job: dict) -> bool:
    """True if the job is clearly irrelevant."""
    text = _text(job)
    return any(neg in text for neg in NEGATIVE_KEYWORDS)


def score_job(job: dict) -> int:
    """
    Return a match score 0–100 based on resume keyword overlap.
    Ceiling: 15 weighted points = 100% (a top ECE job hits ~20+ points,
    so excellent matches cap out, while partial matches show meaningful %s).
    """
    text = _text(job)
    SCORE_CEILING = 15   # weighted points that equals 100%
    earned = 0
    for keyword, weight in RESUME_KEYWORDS.items():
        if keyword in text:
            earned += weight
    score = int((earned / SCORE_CEILING) * 100)
    return min(score, 100)


def get_tags(job: dict) -> list[str]:
    """Extract matched resume keywords as tags for the UI."""
    text = _text(job)
    found = []
    # Prioritise high-weight keywords first
    sorted_kw = sorted(RESUME_KEYWORDS.items(), key=lambda x: -x[1])
    for keyword, _ in sorted_kw:
        if keyword in text and keyword not in found:
            found.append(keyword)
        if len(found) >= 6:
            break
    return found


def classify_category(job: dict) -> str:
    """Assign job to one of the UI filter categories."""
    text = _text(job)
    for cat, keywords in JOB_CATEGORIES.items():
        if any(kw in text for kw in keywords):
            return cat
    return "Hardware"   # sensible ECE default


def process_job(raw: dict) -> dict | None:
    """
    Score, filter, and enrich a raw job dict.
    Returns None if the job should be discarded.
    """
    if is_negative(raw):
        return None

    score = score_job(raw)
    if score < MIN_MATCH_SCORE:
        return None

    raw["match_score"] = score
    raw["tags"]        = json.dumps(get_tags(raw))
    raw["category"]    = classify_category(raw)
    return raw
