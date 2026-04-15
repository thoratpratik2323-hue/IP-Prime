"""
IP Prime — Persistent Chat History

Saves conversation messages to SQLite so history survives WebSocket reconnects.
Uses the same DB as memory.py (data/ipprime.db).
"""

import json
import logging
import sqlite3
import time
from pathlib import Path

log = logging.getLogger("ipprime.chat_history")

DB_PATH = Path(__file__).parent / "data" / "ipprime.db"


def _get_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_chat_tables():
    """Create chat history tables if they don't exist."""
    conn = _get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at REAL NOT NULL,
            ended_at REAL,
            summary TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            role TEXT NOT NULL,          -- 'user' or 'assistant'
            content TEXT NOT NULL,
            timestamp REAL NOT NULL,
            FOREIGN KEY(session_id) REFERENCES chat_sessions(id)
        );
    """)
    conn.close()
    log.info("Chat history tables initialized")


def start_session() -> int:
    """Start a new chat session. Returns session ID."""
    conn = _get_db()
    cur = conn.execute(
        "INSERT INTO chat_sessions (started_at) VALUES (?)",
        (time.time(),)
    )
    session_id = cur.lastrowid
    conn.commit()
    conn.close()
    log.info(f"Started chat session {session_id}")
    return session_id


def end_session(session_id: int, summary: str = ""):
    """Mark a session as ended."""
    conn = _get_db()
    conn.execute(
        "UPDATE chat_sessions SET ended_at = ?, summary = ? WHERE id = ?",
        (time.time(), summary, session_id)
    )
    conn.commit()
    conn.close()


def save_message(session_id: int, role: str, content: str):
    """Save a single message to the current session."""
    conn = _get_db()
    conn.execute(
        "INSERT INTO chat_messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
        (session_id, role, content, time.time())
    )
    conn.commit()
    conn.close()


def save_messages_batch(session_id: int, messages: list[dict]):
    """Save multiple messages at once (more efficient)."""
    if not messages:
        return
    conn = _get_db()
    now = time.time()
    conn.executemany(
        "INSERT INTO chat_messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
        [(session_id, m["role"], m["content"], now) for m in messages]
    )
    conn.commit()
    conn.close()


def load_recent_messages(limit: int = 20) -> list[dict]:
    """Load the most recent messages across sessions.
    
    Returns messages in chronological order (oldest first).
    Intelligently loads from the last session(s) to fill the limit.
    """
    conn = _get_db()
    results = conn.execute(
        """SELECT role, content FROM chat_messages 
           ORDER BY timestamp DESC LIMIT ?""",
        (limit,)
    ).fetchall()
    conn.close()
    
    messages = [{"role": r["role"], "content": r["content"]} for r in reversed(results)]
    return messages


def load_last_session_summary() -> str:
    """Load the summary from the most recent session."""
    conn = _get_db()
    result = conn.execute(
        "SELECT summary FROM chat_sessions WHERE summary != '' ORDER BY started_at DESC LIMIT 1"
    ).fetchone()
    conn.close()
    return result["summary"] if result else ""


def get_session_count() -> int:
    """Get total number of sessions."""
    conn = _get_db()
    result = conn.execute("SELECT COUNT(*) as cnt FROM chat_sessions").fetchone()
    conn.close()
    return result["cnt"]


def get_message_count(session_id: int = None) -> int:
    """Get total messages, optionally for a specific session."""
    conn = _get_db()
    if session_id:
        result = conn.execute(
            "SELECT COUNT(*) as cnt FROM chat_messages WHERE session_id = ?",
            (session_id,)
        ).fetchone()
    else:
        result = conn.execute("SELECT COUNT(*) as cnt FROM chat_messages").fetchone()
    conn.close()
    return result["cnt"]


# Initialize on import
init_chat_tables()
