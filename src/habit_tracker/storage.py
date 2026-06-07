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


# ── Migrations ──────────────────────────────────────────────────────────────
#
# Versioned schema evolution keyed off SQLite's `PRAGMA user_version`. Each entry
# in _MIGRATIONS upgrades the DB by exactly one version; index i takes the DB from
# version i to i+1. init_db() applies every migration with index >= the stored
# version, then sets user_version to len(_MIGRATIONS). Append-only — never edit or
# reorder an existing migration, or deployed databases will diverge.


def _migration_0001_base(con: sqlite3.Connection) -> None:
    """Initial schema + the historical `notes` column on entries."""
    con.executescript(_SCHEMA)
    cols = {row[1] for row in con.execute("PRAGMA table_info(entries)")}
    if "notes" not in cols:
        con.execute("ALTER TABLE entries ADD COLUMN notes TEXT")


def _migration_0002_schedule_category(con: sqlite3.Connection) -> None:
    """Add habit frequency (schedule) and grouping (category) columns."""
    cols = {row[1] for row in con.execute("PRAGMA table_info(habits)")}
    if "schedule" not in cols:
        con.execute("ALTER TABLE habits ADD COLUMN schedule TEXT")
    if "category" not in cols:
        con.execute("ALTER TABLE habits ADD COLUMN category TEXT")


# Ordered list; index i migrates user_version i -> i+1.
_MIGRATIONS = [
    _migration_0001_base,
    _migration_0002_schedule_category,
]

# Canonical habit column order shared by all SELECTs and _row_to_habit.
_HABIT_COLS = "id,name,emoji,color,target,created_at,archived,schedule,category"


def init_db() -> None:
    """Create or upgrade the database to the latest schema version (idempotent)."""
    with _conn() as con:
        version = con.execute("PRAGMA user_version").fetchone()[0]
        for migrate in _MIGRATIONS[version:]:
            migrate(con)
        if version != len(_MIGRATIONS):
            con.execute(f"PRAGMA user_version = {len(_MIGRATIONS)}")


# ── Habits ────────────────────────────────────────────────────────────────────

def create_habit(
    name: str,
    emoji: str = "",
    color: str = "green",
    target: int | None = None,
    schedule: str | None = None,
    category: str | None = None,
) -> Habit:
    today = date.today().isoformat()
    with _conn() as con:
        cur = con.execute(
            "INSERT INTO habits (name, emoji, color, target, created_at, schedule, category) "
            "VALUES (?,?,?,?,?,?,?)",
            (name, emoji, color, target, today, schedule, category),
        )
        return Habit(
            id=cur.lastrowid,  # type: ignore[arg-type]
            name=name,
            emoji=emoji,
            color=color,
            target=target,
            created_at=date.today(),
            schedule=schedule,
            category=category,
        )


def get_habit(name: str) -> Habit | None:
    with _conn() as con:
        row = con.execute(
            f"SELECT {_HABIT_COLS} FROM habits WHERE name=?",
            (name,),
        ).fetchone()
    return _row_to_habit(row) if row else None


def get_habit_by_id(habit_id: int) -> Habit | None:
    with _conn() as con:
        row = con.execute(
            f"SELECT {_HABIT_COLS} FROM habits WHERE id=?",
            (habit_id,),
        ).fetchone()
    return _row_to_habit(row) if row else None


def list_habits(include_archived: bool = False) -> list[Habit]:
    with _conn() as con:
        if include_archived:
            rows = con.execute(
                f"SELECT {_HABIT_COLS} FROM habits ORDER BY id"
            ).fetchall()
        else:
            rows = con.execute(
                f"SELECT {_HABIT_COLS} FROM habits WHERE archived=0 ORDER BY id"
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


_UNSET = object()


def update_habit(
    habit_id: int,
    *,
    name: str | None = None,
    emoji: str | None = None,
    color: str | None = None,
    target: int | None | object = _UNSET,
    schedule: str | None | object = _UNSET,
    category: str | None | object = _UNSET,
) -> Habit | None:
    """Update the provided fields on a habit; unspecified fields are left unchanged.

    Pass ``target``/``schedule``/``category=None`` explicitly to clear them (the _UNSET
    sentinel distinguishes "leave alone" from "set to NULL"). Returns the updated Habit,
    or None if no such habit. Raises sqlite3.IntegrityError on a name collision.
    """
    sets: list[str] = []
    params: list = []
    if name is not None:
        sets.append("name=?")
        params.append(name)
    if emoji is not None:
        sets.append("emoji=?")
        params.append(emoji)
    if color is not None:
        sets.append("color=?")
        params.append(color)
    if target is not _UNSET:
        sets.append("target=?")
        params.append(target)
    if schedule is not _UNSET:
        sets.append("schedule=?")
        params.append(schedule)
    if category is not _UNSET:
        sets.append("category=?")
        params.append(category)

    if sets:
        params.append(habit_id)
        with _conn() as con:
            con.execute(f"UPDATE habits SET {', '.join(sets)} WHERE id=?", params)
    return get_habit_by_id(habit_id)


def _row_to_habit(row: tuple) -> Habit:
    return Habit(
        id=row[0],
        name=row[1],
        emoji=row[2],
        color=row[3],
        target=row[4],
        created_at=date.fromisoformat(row[5]),
        archived=bool(row[6]),
        schedule=row[7],
        category=row[8],
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
