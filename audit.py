"""
IP Prime — Activity Audit Log

A tamper-aware system log that records every action Prime takes.
Provides a searchable history of what happened, when, and why.

Stores:
- Every command executed
- Every file touched
- Every API call made
- Every memory stored
- Every agent spawned
"""

import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Optional

log = logging.getLogger("ipprime.audit")

AUDIT_DB_PATH = Path(__file__).parent / "data" / "audit.db"


def _get_audit_db() -> sqlite3.Connection:
    AUDIT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(AUDIT_DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   REAL NOT NULL,
            category    TEXT NOT NULL,  -- command, file, api, memory, agent, system
            action      TEXT NOT NULL,  -- what happened
            detail      TEXT,           -- extra JSON detail
            user_input  TEXT,           -- what triggered it (if user-initiated)
            status      TEXT DEFAULT 'ok'  -- ok | error | warning
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS audit_timestamp_idx ON audit_log(timestamp)
    """)
    conn.commit()
    return conn


def audit_log(
    category: str,
    action: str,
    detail: Optional[dict] = None,
    user_input: Optional[str] = None,
    status: str = "ok",
):
    """Write a single audit entry. Fire-and-forget — never raises."""
    try:
        conn = _get_audit_db()
        conn.execute(
            "INSERT INTO audit_log (timestamp, category, action, detail, user_input, status) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                time.time(),
                category,
                action,
                json.dumps(detail) if detail else None,
                user_input,
                status,
            )
        )
        conn.commit()
        conn.close()
    except Exception as e:
        log.debug(f"Audit write failed: {e}")  # silent — never crash the main flow


def get_audit_history(limit: int = 50, category: Optional[str] = None) -> list[dict]:
    """Retrieve recent audit entries, optionally filtered by category."""
    try:
        conn = _get_audit_db()
        if category:
            rows = conn.execute(
                "SELECT * FROM audit_log WHERE category = ? ORDER BY timestamp DESC LIMIT ?",
                (category, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        log.debug(f"Audit read failed: {e}")
        return []


def format_audit_report(entries: list[dict]) -> str:
    """Format audit entries as a human-readable report for Prime to speak."""
    if not entries:
        return "No audit records found."

    lines = ["PRIME ACTIVITY AUDIT LOG", "=" * 40]
    for e in entries:
        ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(e["timestamp"]))
        status_icon = "✅" if e["status"] == "ok" else "⚠️" if e["status"] == "warning" else "❌"
        lines.append(f"{status_icon} [{ts}] [{e['category'].upper()}] {e['action']}")
        if e.get("user_input"):
            lines.append(f"   Triggered by: \"{e['user_input'][:60]}\"")
    return "\n".join(lines)
