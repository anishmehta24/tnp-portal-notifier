"""SQLite persistence. Idempotent: re-inserting a seen uid is a no-op, so the
same item is never processed twice. `notified` tracks delivery so a failed send
is retried next cycle (never-miss-an-alert)."""
import sqlite3
from contextlib import contextmanager

import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS notifications (
    uid         TEXT PRIMARY KEY,
    title       TEXT,
    category    TEXT,
    description TEXT,
    posted_at   TEXT,
    url         TEXT,
    first_seen  TEXT DEFAULT (datetime('now')),
    notified    INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS companies (
    uid        TEXT PRIMARY KEY,
    name       TEXT,
    deadline   TEXT,
    posted_on  TEXT,
    url        TEXT,
    first_seen TEXT DEFAULT (datetime('now')),
    notified   INTEGER DEFAULT 0
);
"""

_TABLE = {"notifications": "notifications", "companies": "companies"}


@contextmanager
def _conn():
    con = sqlite3.connect(config.DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()


def init_db():
    with _conn() as con:
        con.executescript(SCHEMA)


def known_uids(table: str) -> set[str]:
    t = _TABLE[table]
    with _conn() as con:
        return {r[0] for r in con.execute(f"SELECT uid FROM {t}")}


def insert(table: str, rows: list[dict]):
    """Insert new rows, ignoring any uid already present."""
    if not rows:
        return
    t = _TABLE[table]
    cols = [c for c in rows[0] if c != "uid"] + ["uid"]
    placeholders = ", ".join("?" for _ in cols)
    sql = f"INSERT OR IGNORE INTO {t} ({', '.join(cols)}) VALUES ({placeholders})"
    with _conn() as con:
        con.executemany(sql, [[r[c] for c in cols] for r in rows])


def mark_notified(table: str, uids: list[str]):
    if not uids:
        return
    t = _TABLE[table]
    with _conn() as con:
        con.executemany(
            f"UPDATE {t} SET notified = 1 WHERE uid = ?", [(u,) for u in uids]
        )


def pending_notifications(table: str) -> list[dict]:
    """Rows stored but not yet successfully delivered."""
    t = _TABLE[table]
    with _conn() as con:
        return [dict(r) for r in con.execute(
            f"SELECT * FROM {t} WHERE notified = 0 ORDER BY first_seen"
        )]
