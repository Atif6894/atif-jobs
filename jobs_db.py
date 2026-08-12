import sqlite3
import json
from datetime import datetime
from typing import Optional

DB_PATH = "atif_jobs.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id          TEXT PRIMARY KEY,
            title       TEXT NOT NULL,
            company     TEXT NOT NULL,
            location    TEXT,
            description TEXT,
            url         TEXT UNIQUE NOT NULL,
            salary      TEXT,
            source      TEXT,
            category    TEXT,
            tags        TEXT,
            match_score INTEGER DEFAULT 0,
            posted_at   TEXT,
            fetched_at  TEXT NOT NULL,
            is_saved    INTEGER DEFAULT 0,
            is_applied  INTEGER DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS meta (
            key   TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    conn.commit()
    conn.close()

def upsert_job(job: dict):
    conn = get_connection()
    try:
        conn.execute("""
            INSERT OR IGNORE INTO jobs
            (id, title, company, location, description, url, salary, source,
             category, tags, match_score, posted_at, fetched_at)
            VALUES
            (:id, :title, :company, :location, :description, :url, :salary, :source,
             :category, :tags, :match_score, :posted_at, :fetched_at)
        """, job)
        conn.commit()
    finally:
        conn.close()

def get_jobs(
    category: Optional[str] = None,
    location: Optional[str] = None,
    source: Optional[str] = None,
    min_score: int = 0,
    sort_by: str = "match_score",   # match_score | posted_at
    limit: int = 200,
) -> list[dict]:
    conn = get_connection()
    try:
        query = "SELECT * FROM jobs WHERE match_score >= ?"
        params: list = [min_score]

        if category and category != "All":
            query += " AND category = ?"
            params.append(category)
        if location and location != "All":
            query += " AND location LIKE ?"
            params.append(f"%{location}%")
        if source and source != "All":
            query += " AND source = ?"
            params.append(source)

        order = "match_score DESC" if sort_by == "match_score" else "posted_at DESC"
        query += f" ORDER BY {order} LIMIT ?"
        params.append(limit)

        rows = conn.execute(query, params).fetchall()
        result = []
        for row in rows:
            d = dict(row)
            d["tags"] = json.loads(d["tags"]) if d["tags"] else []
            result.append(d)
        return result
    finally:
        conn.close()

def get_stats() -> dict:
    conn = get_connection()
    try:
        total   = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        high    = conn.execute("SELECT COUNT(*) FROM jobs WHERE match_score >= 70").fetchone()[0]
        medium  = conn.execute("SELECT COUNT(*) FROM jobs WHERE match_score >= 40 AND match_score < 70").fetchone()[0]
        low     = conn.execute("SELECT COUNT(*) FROM jobs WHERE match_score >= 25 AND match_score < 40").fetchone()[0]
        sources = conn.execute("SELECT source, COUNT(*) as cnt FROM jobs GROUP BY source").fetchall()
        last_updated = conn.execute("SELECT value FROM meta WHERE key='last_updated'").fetchone()
        return {
            "total": total,
            "high_match": high,
            "medium_match": medium,
            "low_match": low,
            "sources": {r["source"]: r["cnt"] for r in sources},
            "last_updated": last_updated[0] if last_updated else None,
        }
    finally:
        conn.close()

def set_meta(key: str, value: str):
    conn = get_connection()
    conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def toggle_saved(job_id: str, saved: bool):
    conn = get_connection()
    conn.execute("UPDATE jobs SET is_saved = ? WHERE id = ?", (1 if saved else 0, job_id))
    conn.commit()
    conn.close()

def delete_old_jobs(days: int = 30):
    """Remove jobs older than N days"""
    conn = get_connection()
    conn.execute(
        "DELETE FROM jobs WHERE fetched_at < datetime('now', ?)",
        (f"-{days} days",)
    )
    conn.commit()
    conn.close()
