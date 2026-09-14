"""Persistent Session State (Criteria 7).

Manages persistent conversational and architectural project state across turns
using a persistent database store, enabling cross-session recall and project continuity.
"""

import json
import sqlite3
from typing import Any, Dict, List, Optional
from app.observability.logging import get_logger
from app.observability.pii import redact_pii

logger = get_logger("app.memory.session_store")


class PersistentSessionStore:
    """Persistent storage engine for agent sessions and architectural project states."""

    def __init__(self, db_path: str = "sessions.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initializes database tables for sessions and project memories."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    project_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata_json TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    role TEXT,
                    content TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS parcel_cache (
                    cadastral_reference TEXT PRIMARY KEY,
                    municipality TEXT,
                    area_sqm REAL,
                    geometry_json TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def save_message(self, session_id: str, role: str, content: str) -> None:
        """Saves a message to persistent storage with PII redaction."""
        clean_content = redact_pii(content)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
                (session_id, role, clean_content),
            )
            cursor.execute(
                "UPDATE sessions SET updated_at = CURRENT_TIMESTAMP WHERE session_id = ?",
                (session_id,),
            )
            conn.commit()
        logger.info("session_message_persisted", session_id=session_id, role=role)

    def get_messages(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves conversational history for a session."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT role, content, timestamp FROM messages WHERE session_id = ? ORDER BY id ASC LIMIT ?",
                (session_id, limit),
            )
            rows = cursor.fetchall()
            return [{"role": r[0], "content": r[1], "timestamp": r[2]} for r in rows]

    def save_parcel_state(self, cadastral_reference: str, municipality: str, area_sqm: float, geometry: Dict[str, Any]) -> None:
        """Caches parcel geometry state to database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO parcel_cache (cadastral_reference, municipality, area_sqm, geometry_json)
                VALUES (?, ?, ?, ?)
                """,
                (cadastral_reference, municipality, area_sqm, json.dumps(geometry)),
            )
            conn.commit()


_global_session_store: Optional[PersistentSessionStore] = None


def get_session_store(db_path: str = "sessions.db") -> PersistentSessionStore:
    """Returns singleton instance of PersistentSessionStore."""
    global _global_session_store
    if _global_session_store is None:
        _global_session_store = PersistentSessionStore(db_path)
    return _global_session_store
