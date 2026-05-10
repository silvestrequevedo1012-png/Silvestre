"""
models/database.py
Handles SQLite connection and schema creation.
DB path is read from SIS_DB_PATH env var (set by main.py before any imports),
falling back to a path relative to this file so direct model tests still work.
"""

import sqlite3
import os

# main.py sets this env var to an absolute path before importing anything
_env_path = os.environ.get("SIS_DB_PATH", "")
if _env_path:
    DB_PATH = _env_path
else:
    # Fallback: two levels up from models/database.py -> project root
    DB_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sis.db"
    )


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_db():
    """Create all tables if they don't exist."""
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT    NOT NULL UNIQUE,
            password TEXT    NOT NULL,
            name     TEXT    NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            id_number         TEXT NOT NULL UNIQUE,
            first_name        TEXT NOT NULL,
            last_name         TEXT NOT NULL,
            middle_name       TEXT,
            birthdate         TEXT,
            gender            TEXT,
            address           TEXT,
            phone             TEXT,
            email             TEXT,
            password          TEXT NOT NULL,
            course            TEXT,
            block             TEXT,
            year_level        TEXT,
            guardian_name     TEXT,
            guardian_relation TEXT,
            guardian_phone    TEXT,
            logged_in         INTEGER DEFAULT 0,
            photo             TEXT,
            created_at        TEXT    DEFAULT (datetime('now','localtime'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS faculty (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            id_number   TEXT NOT NULL UNIQUE,
            first_name  TEXT NOT NULL,
            last_name   TEXT NOT NULL,
            middle_name TEXT,
            birthdate   TEXT,
            gender      TEXT,
            address     TEXT,
            phone       TEXT,
            email       TEXT,
            password    TEXT NOT NULL,
            department  TEXT,
            position    TEXT,
            logged_in   INTEGER DEFAULT 0,
            photo       TEXT,
            created_at  TEXT    DEFAULT (datetime('now','localtime'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS schedules (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id   TEXT NOT NULL,
            owner_type TEXT NOT NULL CHECK(owner_type IN ('student','faculty')),
            day        TEXT NOT NULL,
            subject    TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time   TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL DEFAULT (datetime('now','localtime')),
            id_number TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role      TEXT NOT NULL,
            action    TEXT NOT NULL CHECK(action IN ('ENTRY','EXIT')),
            status    TEXT NOT NULL,
            subject   TEXT
        )
    """)

    c.execute("""
        INSERT OR IGNORE INTO admins (username, password, name)
        VALUES ('admin', 'admin123', 'System Administrator')
    """)

    conn.commit()
    conn.close()


def migrate_db():
    """Add missing columns to existing databases."""
    conn = get_connection()
    for table, col in [('students', 'photo'), ('faculty', 'photo')]:
        try:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} TEXT")
            conn.commit()
        except Exception:
            pass
    conn.close()
