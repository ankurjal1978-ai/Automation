import sqlite3
from pathlib import Path

from app.config import DB_PATH, DATA_DIR


def ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def get_connection():
    ensure_data_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    ensure_data_dir()
    conn = get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT,
                last_name TEXT,
                email TEXT UNIQUE,
                company TEXT,
                title TEXT,
                website TEXT,
                industry TEXT,
                country TEXT,
                campaign TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                source_file TEXT
            )
            """
        )
        conn.commit()
    finally:
        conn.close()
