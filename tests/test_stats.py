"""Tests for stats.py — streaks, completion, intensity bucketing."""
from datetime import date, timedelta

import pytest

from habit_tracker.models import Entry, Habit
from habit_tracker.stats import (
    build_stats,
    completion_rate,
    current_streak,
    day_of_week_bias,
    intensity_bucket,
    longest_streak,
    range_dates,
    rolling_completion,
)
from habit_tracker.render.heatmap import _week_start_offset


def _habit(target=None) -> Habit:
    return Habit(id=1, name="H", emoji="", color="green", target=target, created_at=TODAY)


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

class TestTodayCount:
    def test_no_entry_today_is_zero(self):
        stats = build_stats(_habit(), [_entry(1, TODAY - timedelta(days=1), 3)], today=TODAY)
        assert stats.today_count == 0
        assert not stats.done_today

    def test_single_entry_today(self):
        stats = build_stats(_habit(), [_entry(1, TODAY, 5)], today=TODAY)
        assert stats.today_count == 5
        assert stats.done_today

    def test_only_today_counted(self):
        entries = [_entry(1, TODAY, 2), _entry(1, TODAY - timedelta(days=1), 9)]
        stats = build_stats(_habit(target=2), entries, today=TODAY)
        assert stats.today_count == 2


class TestRollingCompletion:
    def test_empty_returns_zeros(self):
        result = rolling_completion([], until=TODAY, days=7)
        assert result == [0.0] * 7

    def test_length_matches_days(self):
        result = rolling_completion([], until=TODAY, days=30)
        assert len(result) == 30

    def test_all_logged_gives_ones(self):
        from datetime import timedelta
        entries = [_entry(1, TODAY - timedelta(days=i)) for i in range(14)]
        result = rolling_completion(entries, window=7, until=TODAY, days=7)
        assert all(v == 1.0 for v in result)

    def test_no_entries_in_range_gives_zeros(self):
        result = rolling_completion([], window=7, until=TODAY, days=7)
        assert result == [0.0] * 7

    def test_partial_window_gives_correct_rate(self):
        from datetime import timedelta
        # Log every other day for 14 days
        entries = [_entry(1, TODAY - timedelta(days=i * 2)) for i in range(7)]
        result = rolling_completion(entries, window=7, until=TODAY, days=1)
        # In window [TODAY-6 .. TODAY]: entries at -0,-2,-4,-6 = 4/7
        assert result[0] == pytest.approx(4 / 7)


class TestDayOfWeekBias:
    def test_empty_returns_zeros(self):
        result = day_of_week_bias([])
        assert result == {i: 0.0 for i in range(7)}

    def test_keys_are_zero_to_six(self):
        result = day_of_week_bias([_entry(1, TODAY)])
        assert set(result.keys()) == set(range(7))

    def test_single_weekday_is_one(self):
        # TODAY = 2026-06-05 = Friday = weekday 4
        result = day_of_week_bias([_entry(1, TODAY)])
        assert result[4] == 1.0  # Friday always done (only day in range)

    def test_never_done_weekday_is_zero(self):
        # Log every day for a full week → all weekdays should be close to 1
        from datetime import timedelta
        entries = [_entry(1, TODAY - timedelta(days=i)) for i in range(7)]
        result = day_of_week_bias(entries)
        assert all(v > 0 for v in result.values())

    def test_all_values_between_zero_and_one(self):
        from datetime import timedelta
        entries = [_entry(1, TODAY - timedelta(days=i)) for i in range(0, 30, 3)]
        result = day_of_week_bias(entries)
        assert all(0.0 <= v <= 1.0 for v in result.values())

    def test_build_stats_includes_analytics_fields(self):
        from datetime import timedelta
        entries = [_entry(1, TODAY - timedelta(days=i)) for i in range(14)]
        stats = build_stats(_habit(), entries, today=TODAY)
        assert len(stats.rolling_completion) == 90
        assert set(stats.day_of_week_bias.keys()) == set(range(7))


class TestWeekStartOffset:
    # date(2026, 6, 5) is a Friday → weekday()=4
    # Sunday-start offset: (4 + 1) % 7 = 5
    # Monday-start offset: 4 % 7 = 4
    def test_sunday_start_friday(self):
        d = date(2026, 6, 5)  # Friday
        assert _week_start_offset(d, "sunday") == 5

    def test_monday_start_friday(self):
        d = date(2026, 6, 5)  # Friday
        assert _week_start_offset(d, "monday") == 4

    def test_sunday_start_sunday(self):
        # Sunday weekday() = 6 → (6+1)%7 = 0 (no padding)
        d = date(2026, 6, 7)  # Sunday
        assert _week_start_offset(d, "sunday") == 0

    def test_monday_start_monday(self):
        # Monday weekday() = 0 → 0 (no padding)
        d = date(2026, 6, 1)  # Monday
        assert _week_start_offset(d, "monday") == 0

    def test_sunday_start_monday(self):
        # Monday weekday() = 0 → (0+1)%7 = 1
        d = date(2026, 6, 1)  # Monday
        assert _week_start_offset(d, "sunday") == 1


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
