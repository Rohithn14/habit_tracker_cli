"""Tests for Phase 1: update_habit, color validation, import notes round-trip."""
import csv
import json
import sqlite3
from datetime import date

import pytest

from habit_tracker.colors import is_valid_color


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    db_path = tmp_path / "habits.db"
    monkeypatch.setattr("habit_tracker.storage.DB_PATH", db_path)
    monkeypatch.setattr("habit_tracker.config.DATA_DIR", tmp_path)
    from habit_tracker.storage import init_db
    init_db()
    yield db_path


from habit_tracker.storage import (
    create_habit,
    get_entry,
    get_habit,
    log_entry,
    update_habit,
)


class TestUpdateHabit:
    def test_update_single_field(self):
        h = create_habit("run", emoji="🏃", color="green", target=3)
        updated = update_habit(h.id, name="jog")
        assert updated.name == "jog"
        assert updated.emoji == "🏃" and updated.color == "green" and updated.target == 3

    def test_update_multiple_fields(self):
        h = create_habit("read")
        updated = update_habit(h.id, emoji="📚", color="cyan", target=10)
        assert (updated.emoji, updated.color, updated.target) == ("📚", "cyan", 10)

    def test_clear_target(self):
        h = create_habit("water", target=8)
        updated = update_habit(h.id, target=None)
        assert updated.target is None

    def test_leave_target_unchanged_when_omitted(self):
        h = create_habit("water", target=8)
        updated = update_habit(h.id, emoji="💧")
        assert updated.target == 8

    def test_name_collision_raises(self):
        create_habit("a")
        b = create_habit("b")
        with pytest.raises(sqlite3.IntegrityError):
            update_habit(b.id, name="a")

    def test_unknown_id_returns_none(self):
        assert update_habit(9999, emoji="x") is None


class TestColorValidation:
    def test_known_colors(self):
        assert is_valid_color("green")
        assert is_valid_color("violet")

    def test_unknown_color(self):
        assert not is_valid_color("chartreuse")
        assert not is_valid_color("")


class TestImportNotesRoundTrip:
    def test_json_import_preserves_notes(self):
        from habit_tracker.cli import import_cmd
        h = create_habit("meditate")
        payload = [{
            "name": "meditate",
            "entries": [{"date": "2026-06-01", "count": 2, "notes": "calm session"}],
        }]
        path = self._write(json.dumps(payload), ".json")
        import_cmd(path, fmt=None, overwrite=True)
        e = get_entry(get_habit("meditate").id, date(2026, 6, 1))
        assert e.count == 2 and e.notes == "calm session"

    def test_csv_import_creates_habit_and_notes(self):
        from habit_tracker.cli import import_cmd
        content = (
            "habit_name,emoji,target,date,count,notes\n"
            "pushups,💪,20,2026-06-02,15,morning set\n"
        )
        path = self._write(content, ".csv")
        import_cmd(path, fmt=None, overwrite=True)
        h = get_habit("pushups")
        assert h is not None and h.emoji == "💪" and h.target == 20
        e = get_entry(h.id, date(2026, 6, 2))
        assert e.count == 15 and e.notes == "morning set"

    def _write(self, content: str, suffix: str) -> str:
        import tempfile
        f = tempfile.NamedTemporaryFile("w", suffix=suffix, delete=False, newline="")
        f.write(content)
        f.close()
        return f.name
