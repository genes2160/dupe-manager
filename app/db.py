import sqlite3
from pathlib import Path
from app.settings import settings


def get_conn() -> sqlite3.Connection:
    db_path = Path(settings.SQLITE_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_conn()
    cur = conn.cursor()

    # scan_runs: each scan attempt with timestamp + status
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS scan_runs (
            id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            root_path TEXT NOT NULL,
            extensions TEXT,
            status TEXT NOT NULL,
            total_files INTEGER DEFAULT 0,
            scanned_files INTEGER DEFAULT 0,
            message TEXT
        )
        """
    )

    # duplicates: store groups by key (filename|size)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS duplicates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_id TEXT NOT NULL,
            found_at TEXT NOT NULL,
            dup_key TEXT NOT NULL,
            filename TEXT NOT NULL,
            size_bytes INTEGER NOT NULL,
            path TEXT NOT NULL,
            FOREIGN KEY(scan_id) REFERENCES scan_runs(id)
        )
        """
    )

    # deletions: record what got deleted and why
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS deletions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_id TEXT NOT NULL,
            deleted_at TEXT NOT NULL,
            path TEXT NOT NULL,
            filename TEXT NOT NULL,
            size_bytes INTEGER NOT NULL,
            result TEXT NOT NULL,
            message TEXT,
            FOREIGN KEY(scan_id) REFERENCES scan_runs(id)
        )
        """
    )

    conn.commit()
    conn.close()
