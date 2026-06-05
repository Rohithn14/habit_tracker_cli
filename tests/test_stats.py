"""Tests for stats.py — streaks, completion, intensity bucketing."""
from datetime import date, timedelta

import pytest

from habit_tracker.models import Entry
from habit_tracker.stats import (
    build_stats,
    completion_rate,
    current_streak,
    intensity_bucket,
    longest_streak,
    range_dates,
)


def _entry(habit_id: int, day: date, count: int = 1) -> Entry:
    return Entry(habit_id=habit_id, date=day, count=count)


TODAY = date(2026, 6, 5)


# ── intensity_bucket ──────────────────────────────────────────────────────────

class TestIntensityBucket:
    def test_zero_count_returns_zero(self):
        assert intensity_bucket(0, None) == 0
        assert intensity_bucket(0, 5) == 0

    def test_no_target_binary(self):
        assert intensity_bucket(1, None) == 2
        assert intensity_bucket(10, None) == 2

    def test_target_full_is_four(self):
        assert intensity_bucket(5, 5) == 4
        assert intensity_bucket(10, 5) == 4

    def test_target_75pct(self):
        assert intensity_bucket(4, 5) == 3  # 80% → level 3

    def test_target_50pct(self):
        assert intensity_bucket(3, 6) == 2  # 50% → level 2

    def test_target_below_50pct(self):
        assert intensity_bucket(1, 5) == 1  # 20% → level 1


# ── current_streak ────────────────────────────────────────────────────────────

class TestCurrentStreak:
    def test_empty(self):
        assert current_streak([], TODAY) == 0

    def test_today_only(self):
        e = [_entry(1, TODAY)]
        assert current_streak(e, TODAY) == 1

    def test_consecutive_three(self):
        entries = [_entry(1, TODAY - timedelta(days=i)) for i in range(3)]
        assert current_streak(entries, TODAY) == 3

    def test_gap_breaks_streak(self):
        # Today + 2 days ago (no yesterday)
        entries = [_entry(1, TODAY), _entry(1, TODAY - timedelta(days=2))]
        assert current_streak(entries, TODAY) == 1

    def test_streak_excludes_future(self):
        entries = [_entry(1, TODAY + timedelta(days=1)), _entry(1, TODAY)]
        assert current_streak(entries, TODAY) == 1

    def test_no_entry_today_is_zero(self):
        entries = [_entry(1, TODAY - timedelta(days=1))]
        assert current_streak(entries, TODAY) == 0


# ── longest_streak ────────────────────────────────────────────────────────────

class TestLongestStreak:
    def test_empty(self):
        assert longest_streak([]) == 0

    def test_single(self):
        assert longest_streak([_entry(1, TODAY)]) == 1

    def test_all_consecutive(self):
        entries = [_entry(1, TODAY - timedelta(days=i)) for i in range(7)]
        assert longest_streak(entries) == 7

    def test_two_runs_picks_longer(self):
        # 3-day run and 5-day run with gap
        run1 = [_entry(1, date(2026, 1, 1) + timedelta(days=i)) for i in range(3)]
        run2 = [_entry(1, date(2026, 2, 1) + timedelta(days=i)) for i in range(5)]
        assert longest_streak(run1 + run2) == 5

    def test_duplicate_dates_count_once(self):
        entries = [_entry(1, TODAY), _entry(1, TODAY)]  # duplicate
        assert longest_streak(entries) == 1


# ── completion_rate ───────────────────────────────────────────────────────────

class TestCompletionRate:
    def test_empty(self):
        since = date(2026, 6, 1)
        until = date(2026, 6, 5)
        assert completion_rate([], since, until) == 0.0

    def test_all_days_done(self):
        since = date(2026, 6, 1)
        until = date(2026, 6, 5)
        entries = [_entry(1, since + timedelta(days=i)) for i in range(5)]
        assert completion_rate(entries, since, until) == 1.0

    def test_half_done(self):
        since = date(2026, 6, 1)
        until = date(2026, 6, 4)  # 4 days
        entries = [_entry(1, date(2026, 6, 1)), _entry(1, date(2026, 6, 3))]
        assert completion_rate(entries, since, until) == 0.5

    def test_out_of_range_entries_excluded(self):
        since = date(2026, 6, 1)
        until = date(2026, 6, 5)
        # Entry before range
        entries = [_entry(1, date(2026, 5, 31)), _entry(1, date(2026, 6, 1))]
        assert completion_rate(entries, since, until) == pytest.approx(1 / 5)


# ── range_dates ───────────────────────────────────────────────────────────────

class TestRangeDates:
    def test_year(self):
        since, until = range_dates("year", TODAY)
        assert since == date(2026, 1, 1)
        assert until == TODAY

    def test_quarter_q2(self):
        since, until = range_dates("quarter", date(2026, 5, 15))
        assert since == date(2026, 4, 1)

    def test_quarter_q1(self):
        since, until = range_dates("quarter", date(2026, 2, 20))
        assert since == date(2026, 1, 1)

    def test_month(self):
        since, until = range_dates("month", TODAY)
        assert since == date(2026, 6, 1)
        assert until == TODAY
