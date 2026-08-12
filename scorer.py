import re
import json
from config import RESUME_KEYWORDS, NEGATIVE_KEYWORDS, JOB_CATEGORIES, MIN_MATCH_SCORE

# Keywords that make a title clearly non-ECE (checked against title only)
TITLE_NEGATIVE = [
    "marketing", "sales", "finance", "accounting", "legal", "lawyer",
    "content", "seo", "recruiter", "hr ", "human resource", "copywriter",
    "graphic", "social media", "brand", "growth hacker", "product manager",
    "business development", "operations manager", "customer success",
    "customer support", "data analyst", "data scientist", "machine learning",
    "devops", "frontend", "backend", "full stack", "java developer",
    "python developer", "react", "angular", "node.js",
]

# Title keywords that confirm it IS an ECE/relevant job
TITLE_POSITIVE = [
    "embedded", "firmware", "hardware", "electronics", "iot", "vlsi",
    "fpga", "pcb", "robotics", "rf ", "antenna", "telecom", "defence",
    "defense", "microcontroller", "signal", "circuit", "semiconductor",
    "electrical", "ece", "engineer", "developer", "technician",
    "automation", "control", "instrumentation", "power", "mechatronics",
]


def _text(job: dict) -> str:
    """Combine title + description into one searchable blob."""
    return (
        (job.get("title") or "") + " " +
        (job.get("description") or "") + " " +
        (job.get("company") or "")
    ).lower()


def _title(job: dict) -> str:
    return (job.get("title") or "").lower()


def is_negative(job: dict) -> bool:
    """True if the job is clearly irrelevant — checks description AND title."""
    text  = _text(job)
    title = _title(job)
    # Reject if description has broad negative phrases
    if any(neg in text for neg in NEGATIVE_KEYWORDS):
        return True
    # Reject if TITLE itself contains clearly non-ECE terms
    if any(neg in title for neg in TITLE_NEGATIVE):
        return True
    return False


def score_job(job: dict) -> int:
    """
    Score 0-100 based on resume keyword overlap.
    Ceiling = 15 weighted points = 100%.
    Jobs with NO ECE keywords in the title get a 40% penalty.
    """
    text  = _text(job)
    title = _title(job)
    SCORE_CEILING = 15
    earned = 0
    for keyword, weight in RESUME_KEYWORDS.items():
        if keyword in text:
            earned += weight
    score = int((earned / SCORE_CEILING) * 100)
    # Penalise if the job title has no ECE relevance at all
    if not any(pos in title for pos in TITLE_POSITIVE):
        score = int(score * 0.4)
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
