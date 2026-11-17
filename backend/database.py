import json
import sqlite3
from datetime import datetime, timedelta
from urllib.parse import urlparse

DB_FILE = "reports.db"
CACHE_DAYS = 7

def get_connection():
    """Open the database. Rows come back like dictionaries (row["domain"])."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def setup_database():
    """Create the reports table if it doesn't exist yet."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT NOT NULL,
                brand_name TEXT,
                logo_url TEXT,
                mode TEXT,
                created_at TEXT NOT NULL,
                report TEXT NOT NULL
            )
        """)

def clean_domain(url):
    """'https://www.example.com/en' to 'example.com', so the same site always matches."""
    url = url.strip().lower()
    if not url.startswith("http"):
        url = "https://" + url
    return urlparse(url).netloc.removeprefix("www.")

def save_report(url, report):
    """Save a finished report. Returns its new ID."""
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO reports (domain, brand_name, logo_url, mode, created_at, report) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                clean_domain(url),
                report.get("brand_name"),
                report.get("logo_url"),
                report.get("mode"),
                datetime.now().isoformat(timespec="seconds"),
                json.dumps(report, ensure_ascii=False),
            ),
        )
        return cursor.lastrowid

def find_cached_report(url):
    """Return the newest saved report for this site from the last 7 days, or None."""
    oldest_allowed = (datetime.now() - timedelta(days=CACHE_DAYS)).isoformat(timespec="seconds")

    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, created_at, report FROM reports "
            "WHERE domain = ? AND created_at >= ? "
            "ORDER BY created_at DESC LIMIT 1",
            (clean_domain(url), oldest_allowed),
        ).fetchone()

    if not row:
        return None

    report = json.loads(row["report"])
    report["from_cache"] = True
    report["cached_at"] = row["created_at"]
    report["history_id"] = row["id"]
    return report

def list_history(limit=50):
    """Short info about saved reports, newest first (for the history page)."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, domain, brand_name, logo_url, mode, created_at FROM reports "
            "ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]

def get_report(report_id):
    """The full saved report with this ID, or None."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, created_at, report FROM reports WHERE id = ?",
            (report_id,),
        ).fetchone()

    if not row:
        return None

    report = json.loads(row["report"])
    report["history_id"] = row["id"]
    report["cached_at"] = row["created_at"]
    return report