"""Tests for schedule parsing, schedule-aware stats, and custom date ranges."""
from datetime import date, timedelta

import pytest

from habit_tracker.models import Entry, Habit
from habit_tracker.schedule import (
    is_due,
    is_valid_schedule,
    parse_schedule,
    scheduled_completion_rate,
    scheduled_current_streak,
    scheduled_longest_streak,
)
from habit_tracker.stats import range_dates

TODAY = date(2026, 6, 5)  # a Friday


def _entries(habit_id: int, days: list[date], count: int = 1) -> list[Entry]:
    return [Entry(habit_id=habit_id, date=d, count=count) for d in days]


class TestParseSchedule:
    def test_daily_default(self):
        assert parse_schedule(None) == ("daily", None)
        assert parse_schedule("daily") == ("daily", None)

    def test_dow(self):
        kind, days = parse_schedule("dow:1,3,5")
        assert kind == "dow"
        assert days == {0, 2, 4}  # Mon, Wed, Fri (0-indexed)

    def test_weekly(self):
        assert parse_schedule("weekly:3") == ("weekly", 3)

    def test_garbage_falls_back_to_daily(self):
        assert parse_schedule("weekley:3")[0] == "daily"
        assert parse_schedule("dow:")[0] == "daily"
        assert parse_schedule("weekly:0")[0] == "daily"

    def test_validation(self):
        assert is_valid_schedule(None)
        assert is_valid_schedule("daily")
        assert is_valid_schedule("weekly:2")
        assert is_valid_schedule("dow:2,4")
        assert not is_valid_schedule("weekley:2")
        assert not is_valid_schedule("dow:abc")


class TestIsDue:
    def test_daily_always_due(self):
        assert is_due(None, TODAY)

    def test_dow_due_only_on_listed_days(self):
        # Fri = ISO 5
        assert is_due("dow:5", TODAY)
        assert not is_due("dow:1", TODAY)  # Monday only


class TestScheduledCompletion:
    def test_daily_matches_plain_rate(self):
        days = [TODAY - timedelta(days=i) for i in range(5)]  # 5 of last 10
        rate = scheduled_completion_rate(_entries(1, days), TODAY - timedelta(days=9), TODAY, None)
        assert rate == pytest.approx(5 / 10)

    def test_dow_only_counts_due_days(self):
        # Mon/Wed/Fri schedule over a 2-week window; complete every Mon/Wed/Fri
        since = date(2026, 6, 1)  # Monday
        until = date(2026, 6, 14)  # Sunday (2 full weeks)
        due = [d for d in (since + timedelta(days=i) for i in range(14)) if d.weekday() in {0, 2, 4}]
        rate = scheduled_completion_rate(_entries(1, due), since, until, "dow:1,3,5")
        assert rate == pytest.approx(1.0)

    def test_weekly_quota(self):
        # weekly:3 — one week with exactly 3 entries → full credit for that week
        since = date(2026, 6, 1)  # Mon
        until = date(2026, 6, 7)  # Sun
        rate = scheduled_completion_rate(
            _entries(1, [date(2026, 6, 1), date(2026, 6, 3), date(2026, 6, 5)]),
            since, until, "weekly:3",
        )
        assert rate == pytest.approx(1.0)

    def test_weekly_partial(self):
        since = date(2026, 6, 1)
        until = date(2026, 6, 7)
        rate = scheduled_completion_rate(
            _entries(1, [date(2026, 6, 1)]), since, until, "weekly:4",
        )
        assert rate == pytest.approx(0.25)


class TestScheduledStreak:
    def test_dow_streak_skips_non_due_days(self):
        # Mon/Wed/Fri; entries on Mon(1), Wed(3), Fri(5) up to today(Fri 5) → streak 3
        days = [date(2026, 6, 1), date(2026, 6, 3), date(2026, 6, 5)]
        streak = scheduled_current_streak(_entries(1, days), TODAY, "dow:1,3,5")
        assert streak == 3

    def test_dow_streak_breaks_on_missed_due_day(self):
        # Missing Wed breaks the streak; only Fri counts
        days = [date(2026, 6, 1), date(2026, 6, 5)]
        streak = scheduled_current_streak(_entries(1, days), TODAY, "dow:1,3,5")
        assert streak == 1

    def test_weekly_streak_counts_met_weeks(self):
        # Two consecutive weeks each hitting weekly:2
        days = [
            date(2026, 5, 25), date(2026, 5, 27),  # week of May 25
            date(2026, 6, 1), date(2026, 6, 3),    # week of Jun 1 (current)
        ]
        streak = scheduled_current_streak(_entries(1, days), TODAY, "weekly:2")
        assert streak == 2

    def test_daily_streak_unchanged(self):
        days = [TODAY - timedelta(days=i) for i in range(4)]
        assert scheduled_current_streak(_entries(1, days), TODAY, None) == 4

    def test_dow_longest_streak(self):
        days = [date(2026, 6, 1), date(2026, 6, 3), date(2026, 6, 5)]
        assert scheduled_longest_streak(_entries(1, days), "dow:1,3,5") == 3


class TestCustomRanges:
    def test_last_n_days(self):
        since, until = range_dates("last:30d", today=TODAY)
        assert until == TODAY
        assert (until - since).days == 29

    def test_last_n_weeks(self):
        since, until = range_dates("last:2w", today=TODAY)
        assert (until - since).days == 13

    def test_explicit_range(self):
        since, until = range_dates("2026-01-01:2026-03-31", today=TODAY)
        assert since == date(2026, 1, 1)
        assert until == date(2026, 3, 31)

    def test_invalid_falls_back_to_year(self):
        since, until = range_dates("garbage", today=TODAY)
        assert since == date(2026, 1, 1)
        assert until == TODAY

    def test_named_ranges_still_work(self):
        since, _ = range_dates("month", today=TODAY)
        assert since == date(2026, 6, 1)
