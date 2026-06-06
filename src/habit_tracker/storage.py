from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import date
from typing import Generator

from .config import DB_PATH, ensure_dirs
from .models import Entry, Habit

_SCHEMA = """
CREATE TABLE IF NOT EXISTS habits (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT    NOT NULL UNIQUE,
    emoji      TEXT    NOT NULL DEFAULT '',
    color      TEXT    NOT NULL DEFAULT 'green',
    target     INTEGER,
    created_at TEXT    NOT NULL,
    archived   INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS entries (
    habit_id   INTEGER NOT NULL REFERENCES habits(id) ON DELETE CASCADE,
    date       TEXT    NOT NULL,
    count      INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (habit_id, date)
);
"""


@contextmanager
def _conn() -> Generator[sqlite3.Connection, None, None]:
    ensure_dirs()
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def init_db() -> None:
    with _conn() as con:
        con.executescript(_SCHEMA)
        # Migration: add notes column to entries if missing (idempotent)
        existing_cols = {row[1] for row in con.execute("PRAGMA table_info(entries)")}
        if "notes" not in existing_cols:
            con.execute("ALTER TABLE entries ADD COLUMN notes TEXT")


# ── Habits ────────────────────────────────────────────────────────────────────

def create_habit(
    name: str,
    emoji: str = "",
    color: str = "green",
    target: int | None = None,
) -> Habit:
    today = date.today().isoformat()
    with _conn() as con:
        cur = con.execute(
            "INSERT INTO habits (name, emoji, color, target, created_at) VALUES (?,?,?,?,?)",
            (name, emoji, color, target, today),
        )
        return Habit(
            id=cur.lastrowid,  # type: ignore[arg-type]
            name=name,
            emoji=emoji,
            color=color,
            target=target,
            created_at=date.today(),
        )


def get_habit(name: str) -> Habit | None:
    with _conn() as con:
        row = con.execute(
            "SELECT id,name,emoji,color,target,created_at,archived FROM habits WHERE name=?",
            (name,),
        ).fetchone()
    return _row_to_habit(row) if row else None


def get_habit_by_id(habit_id: int) -> Habit | None:
    with _conn() as con:
        row = con.execute(
            "SELECT id,name,emoji,color,target,created_at,archived FROM habits WHERE id=?",
            (habit_id,),
        ).fetchone()
    return _row_to_habit(row) if row else None


def list_habits(include_archived: bool = False) -> list[Habit]:
    with _conn() as con:
        if include_archived:
            rows = con.execute(
                "SELECT id,name,emoji,color,target,created_at,archived FROM habits ORDER BY id"
            ).fetchall()
        else:
            rows = con.execute(
                "SELECT id,name,emoji,color,target,created_at,archived FROM habits WHERE archived=0 ORDER BY id"
            ).fetchall()
    return [_row_to_habit(r) for r in rows]


def archive_habit(name: str) -> bool:
    with _conn() as con:
        cur = con.execute("UPDATE habits SET archived=1 WHERE name=?", (name,))
    return cur.rowcount > 0


def delete_habit(name: str) -> bool:
    with _conn() as con:
        cur = con.execute("DELETE FROM habits WHERE name=?", (name,))
    return cur.rowcount > 0


def _row_to_habit(row: tuple) -> Habit:
    return Habit(
        id=row[0],
        name=row[1],
        emoji=row[2],
        color=row[3],
        target=row[4],
        created_at=date.fromisoformat(row[5]),
        archived=bool(row[6]),
    )


# ── Entries ───────────────────────────────────────────────────────────────────

def log_entry(habit_id: int, day: date, count: int = 1, notes: str | None = None) -> Entry:
    with _conn() as con:
        con.execute(
            "INSERT INTO entries (habit_id, date, count, notes) VALUES (?,?,?,?) "
            "ON CONFLICT(habit_id, date) DO UPDATE SET count=excluded.count, "
            "notes=CASE WHEN excluded.notes IS NOT NULL THEN excluded.notes ELSE notes END",
            (habit_id, day.isoformat(), count, notes),
        )
    return Entry(habit_id=habit_id, date=day, count=count, notes=notes)


def set_entry_note(habit_id: int, day: date, note: str) -> None:
    """Upsert an entry's note without changing count (creates a count=1 entry if none exists)."""
    with _conn() as con:
        con.execute(
            "INSERT INTO entries (habit_id, date, count, notes) VALUES (?,?,1,?) "
            "ON CONFLICT(habit_id, date) DO UPDATE SET notes=excluded.notes",
            (habit_id, day.isoformat(), note),
        )


def remove_entry(habit_id: int, day: date) -> bool:
    with _conn() as con:
        cur = con.execute(
            "DELETE FROM entries WHERE habit_id=? AND date=?",
            (habit_id, day.isoformat()),
        )
    return cur.rowcount > 0


def remove_entries_range(habit_id: int, since: date, until: date) -> int:
    """Delete all entries for habit_id between since and until (inclusive). Returns count removed."""
    with _conn() as con:
        cur = con.execute(
            "DELETE FROM entries WHERE habit_id=? AND date>=? AND date<=?",
            (habit_id, since.isoformat(), until.isoformat()),
        )
    return cur.rowcount


def get_entry(habit_id: int, day: date) -> Entry | None:
    with _conn() as con:
        row = con.execute(
            "SELECT habit_id, date, count, notes FROM entries WHERE habit_id=? AND date=?",
            (habit_id, day.isoformat()),
        ).fetchone()
    if row is None:
        return None
    return Entry(habit_id=row[0], date=date.fromisoformat(row[1]), count=row[2], notes=row[3])


def get_entries(
    habit_id: int,
    since: date | None = None,
    until: date | None = None,
) -> list[Entry]:
    clauses = ["habit_id=?"]
    params: list = [habit_id]
    if since:
        clauses.append("date>=?")
        params.append(since.isoformat())
    if until:
        clauses.append("date<=?")
        params.append(until.isoformat())
    sql = f"SELECT habit_id,date,count,notes FROM entries WHERE {' AND '.join(clauses)} ORDER BY date"
    with _conn() as con:
        rows = con.execute(sql, params).fetchall()
    return [Entry(habit_id=r[0], date=date.fromisoformat(r[1]), count=r[2], notes=r[3]) for r in rows]
