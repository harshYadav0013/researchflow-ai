import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


# Database location
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "research.db"


def get_connection():
    DATA_DIR.mkdir(exist_ok=True)

    connection = sqlite3.connect(DB_PATH)

    connection.row_factory = sqlite3.Row

    return connection


def init_db():
    connection = get_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS research_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            thread_id TEXT UNIQUE NOT NULL,
            question TEXT NOT NULL,
            status TEXT NOT NULL,
            draft TEXT,
            critic TEXT,
            final_version TEXT,
            sources TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )

    connection.commit()
    connection.close()


def create_research(
    thread_id: str,
    question: str,
    draft: str = "",
    critic: str = "",
    sources: list | None = None
):
    now = datetime.now(timezone.utc).isoformat()

    connection = get_connection()

    connection.execute(
        """
        INSERT INTO research_history (
            thread_id,
            question,
            status,
            draft,
            critic,
            final_version,
            sources,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            thread_id,
            question,
            "in_review",
            draft,
            critic,
            "",
            json.dumps(sources or []),
            now,
            now
        )
    )

    connection.commit()
    connection.close()


def update_research(
    thread_id: str,
    status: str,
    draft: str = "",
    critic: str = "",
    final_version: str = "",
    sources: list | None = None
):
    now = datetime.now(timezone.utc).isoformat()

    connection = get_connection()

    connection.execute(
        """
        UPDATE research_history
        SET
            status = ?,
            draft = ?,
            critic = ?,
            final_version = ?,
            sources = ?,
            updated_at = ?
        WHERE thread_id = ?
        """,
        (
            status,
            draft,
            critic,
            final_version,
            json.dumps(sources or []),
            now,
            thread_id
        )
    )

    connection.commit()
    connection.close()


def get_all_research():
    connection = get_connection()

    rows = connection.execute(
        """
        SELECT
            id,
            thread_id,
            question,
            status,
            created_at,
            updated_at
        FROM research_history
        ORDER BY created_at DESC
        """
    ).fetchall()

    connection.close()

    return [dict(row) for row in rows]


def get_research(thread_id: str):
    connection = get_connection()

    row = connection.execute(
        """
        SELECT *
        FROM research_history
        WHERE thread_id = ?
        """,
        (thread_id,)
    ).fetchone()

    connection.close()

    if row is None:
        return None

    result = dict(row)

    result["sources"] = json.loads(
        result["sources"] or "[]"
    )

    return result


init_db()