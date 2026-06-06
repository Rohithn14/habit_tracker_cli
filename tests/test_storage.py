"""Tests for storage.py — CRUD and constraints."""
import sqlite3
from datetime import date, timedelta

import pytest

from habit_tracker.models import Habit


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    """Redirect DB to a temp dir so each test gets a fresh database."""
    db_path = tmp_path / "habits.db"
    monkeypatch.setattr("habit_tracker.storage.DB_PATH", db_path)
    monkeypatch.setattr("habit_tracker.config.DATA_DIR", tmp_path)
    from habit_tracker.storage import init_db
    init_db()
    yield db_path


from habit_tracker.storage import (
    archive_habit,
    create_habit,
    delete_habit,
    get_entries,
    get_entry,
    get_habit,
    get_habit_by_id,
    list_habits,
    log_entry,
    remove_entry,
    remove_entries_range,
    set_entry_note,
)

TODAY = date(2026, 6, 5)


class TestHabitCRUD:
    def test_create_and_fetch(self):
        h = create_habit("Exercise", emoji="💪", color="red", target=5)
        assert h.name == "Exercise"
        assert h.emoji == "💪"
        assert h.target == 5
        assert not h.archived

        fetched = get_habit("Exercise")
        assert fetched is not None
        assert fetched.id == h.id

    def test_get_by_id(self):
        h = create_habit("Read")
        fetched = get_habit_by_id(h.id)
        assert fetched is not None
        assert fetched.name == "Read"

    def test_get_nonexistent_returns_none(self):
        assert get_habit("NoSuchHabit") is None

    def test_unique_name_constraint(self):
        create_habit("Unique")
        with pytest.raises(sqlite3.IntegrityError):
            create_habit("Unique")

    def test_list_habits_excludes_archived(self):
        create_habit("Active")
        create_habit("Archived")
        archive_habit("Archived")
        active = list_habits()
        names = [h.name for h in active]
        assert "Active" in names
        assert "Archived" not in names

    def test_list_habits_include_archived(self):
        create_habit("Active")
        create_habit("Archived")
        archive_habit("Archived")
        all_habits = list_habits(include_archived=True)
        names = [h.name for h in all_habits]
        assert "Active" in names
        assert "Archived" in names

    def test_archive_sets_flag(self):
        create_habit("ToArchive")
        archive_habit("ToArchive")
        h = get_habit("ToArchive")
        assert h is not None
        assert h.archived

    def test_delete_removes_habit(self):
        create_habit("ToDelete")
        deleted = delete_habit("ToDelete")
        assert deleted
        assert get_habit("ToDelete") is None

    def test_delete_nonexistent_returns_false(self):
        assert not delete_habit("Ghost")


class TestEntryCRUD:
    def setup_method(self):
        self.h = create_habit("TestHabit")

    def test_log_and_get_entry(self):
        log_entry(self.h.id, TODAY, count=3)
        e = get_entry(self.h.id, TODAY)
        assert e is not None
        assert e.count == 3
        assert e.date == TODAY

    def test_log_upserts_count(self):
        log_entry(self.h.id, TODAY, count=1)
        log_entry(self.h.id, TODAY, count=5)  # overwrite
        e = get_entry(self.h.id, TODAY)
        assert e is not None
        assert e.count == 5

    def test_remove_entry(self):
        log_entry(self.h.id, TODAY)
        removed = remove_entry(self.h.id, TODAY)
        assert removed
        assert get_entry(self.h.id, TODAY) is None

    def test_remove_nonexistent_returns_false(self):
        assert not remove_entry(self.h.id, TODAY)

    def test_get_entries_date_filter(self):
        dates = [TODAY - timedelta(days=i) for i in range(5)]
        for d in dates:
            log_entry(self.h.id, d)

        since = TODAY - timedelta(days=2)
        entries = get_entries(self.h.id, since=since, until=TODAY)
        assert len(entries) == 3  # today, -1, -2

    def test_get_entries_empty(self):
        assert get_entries(self.h.id) == []

    def test_cascade_delete(self):
        """Deleting a habit deletes all its entries."""
        log_entry(self.h.id, TODAY)
        delete_habit(self.h.name)
        assert get_habit(self.h.name) is None


class TestAnnotations:
    def setup_method(self):
        self.h = create_habit("NoteHabit")

    def test_log_entry_with_notes(self):
        e = log_entry(self.h.id, TODAY, notes="felt great")
        fetched = get_entry(self.h.id, TODAY)
        assert fetched is not None
        assert fetched.notes == "felt great"

    def test_set_entry_note_creates_entry(self):
        set_entry_note(self.h.id, TODAY, "first note")
        e = get_entry(self.h.id, TODAY)
        assert e is not None
        assert e.notes == "first note"
        assert e.count == 1

    def test_set_entry_note_updates_existing(self):
        log_entry(self.h.id, TODAY, count=3)
        set_entry_note(self.h.id, TODAY, "updated note")
        e = get_entry(self.h.id, TODAY)
        assert e is not None
        assert e.notes == "updated note"
        assert e.count == 3  # count unchanged

    def test_log_entry_preserves_existing_note_when_notes_none(self):
        log_entry(self.h.id, TODAY, notes="keep me")
        log_entry(self.h.id, TODAY, count=5)  # no notes arg → preserve
        e = get_entry(self.h.id, TODAY)
        assert e is not None
        assert e.notes == "keep me"

    def test_notes_in_get_entries(self):
        log_entry(self.h.id, TODAY, notes="hi")
        entries = get_entries(self.h.id)
        assert entries[0].notes == "hi"

    def test_notes_default_none(self):
        log_entry(self.h.id, TODAY)
        e = get_entry(self.h.id, TODAY)
        assert e is not None
        assert e.notes is None


class TestRangeUndo:
    def setup_method(self):
        self.h = create_habit("RangeHabit")

    def test_remove_entries_range_all(self):
        from datetime import timedelta
        for i in range(5):
            log_entry(self.h.id, TODAY - timedelta(days=i))
        count = remove_entries_range(self.h.id, TODAY - timedelta(days=4), TODAY)
        assert count == 5
        assert get_entries(self.h.id) == []

    def test_remove_entries_range_partial(self):
        from datetime import timedelta
        for i in range(5):
            log_entry(self.h.id, TODAY - timedelta(days=i))
        # Remove only last 2 days
        count = remove_entries_range(self.h.id, TODAY - timedelta(days=1), TODAY)
        assert count == 2
        remaining = get_entries(self.h.id)
        assert len(remaining) == 3

    def test_remove_entries_range_empty_returns_zero(self):
        count = remove_entries_range(self.h.id, TODAY, TODAY)
        assert count == 0
