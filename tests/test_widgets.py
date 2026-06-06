"""Tests for DayDetailWidget._build_content — no app context required."""
from datetime import date

import pytest

from habit_tracker.models import Entry, Habit
from habit_tracker.tui.widgets import DayDetailWidget

_DAY = date(2026, 6, 5)


def _habit(target=None) -> Habit:
    return Habit(id=1, name="H", emoji="", color="green", target=target, created_at=_DAY)


def _entry(count: int, notes: str | None = None) -> Entry:
    return Entry(habit_id=1, date=_DAY, count=count, notes=notes)


def _plain(day, entry, habit) -> str:
    return DayDetailWidget()._build_content(day, entry, habit).plain


class TestDayDetailContent:
    def test_no_entry_shows_no_entry_logged(self):
        assert "No entry logged" in _plain(_DAY, None, _habit())

    def test_zero_count_treated_as_no_entry(self):
        assert "No entry logged" in _plain(_DAY, _entry(0), _habit())

    def test_count_no_target_shows_count(self):
        text = _plain(_DAY, _entry(3), _habit())
        assert "3" in text

    def test_count_with_target_shows_percentage(self):
        text = _plain(_DAY, _entry(2), _habit(target=10))
        assert "2" in text
        assert "10" in text
        assert "20%" in text

    def test_full_target_met_shows_100(self):
        text = _plain(_DAY, _entry(10), _habit(target=10))
        assert "100%" in text

    def test_over_target_capped_at_100(self):
        text = _plain(_DAY, _entry(15), _habit(target=10))
        assert "100%" in text

    def test_today_marker_on_today(self):
        text = _plain(date.today(), _entry(1), _habit())
        assert "today" in text

    def test_no_today_marker_on_past_date(self):
        past = date(2026, 1, 1)
        text = _plain(past, _entry(1), _habit())
        assert "today" not in text

    def test_note_shown_when_present(self):
        text = _plain(_DAY, _entry(1, notes="great session"), _habit())
        assert "great session" in text

    def test_no_note_icon_when_no_notes(self):
        text = _plain(_DAY, _entry(1, notes=None), _habit())
        assert "📝" not in text

    def test_note_shown_even_with_no_target(self):
        text = _plain(_DAY, _entry(1, notes="done it"), _habit())
        assert "done it" in text

    def test_date_label_in_output(self):
        text = _plain(_DAY, None, _habit())
        assert "Friday" in text or "05 Jun 2026" in text
