"""Habit frequency/scheduling, encoded as a string on Habit.schedule.

Forms (case-insensitive):
  - ``daily`` / ``None`` / unrecognized → due every day (default).
  - ``dow:1,3,5``                       → due on specific ISO weekdays (1=Mon … 7=Sun).
  - ``weekly:N``                        → due N times within each ISO calendar week.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Literal, Sequence

# Parsed form: (kind, param). param is a weekday set for "dow", an int for "weekly",
# and None for "daily".
ScheduleKind = Literal["daily", "dow", "weekly"]


def parse_schedule(schedule: str | None) -> tuple[ScheduleKind, object]:
    if not schedule:
        return ("daily", None)
    s = schedule.strip().lower()
    if s.startswith("dow:"):
        try:
            # ISO 1=Mon..7=Sun → weekday() 0=Mon..6=Sun
            days = {int(p) - 1 for p in s[4:].split(",") if p.strip()}
            days = {d for d in days if 0 <= d <= 6}
        except ValueError:
            return ("daily", None)
        return ("dow", days) if days else ("daily", None)
    if s.startswith("weekly:"):
        try:
            n = int(s[7:])
        except ValueError:
            return ("daily", None)
        return ("weekly", n) if n > 0 else ("daily", None)
    return ("daily", None)


def is_valid_schedule(schedule: str | None) -> bool:
    """True if the string is None/empty or parses to a non-default schedule, or is
    literally 'daily'. Used to reject typos like 'weekley:3' at input boundaries."""
    if not schedule:
        return True
    s = schedule.strip().lower()
    if s == "daily":
        return True
    kind, _ = parse_schedule(s)
    return kind != "daily"


def is_due(schedule: str | None, day: date) -> bool:
    """Whether the schedule expects activity on ``day``. Weekly schedules treat every
    day as an opportunity (the quota is enforced per week, not per day)."""
    kind, param = parse_schedule(schedule)
    if kind == "dow":
        return day.weekday() in param  # type: ignore[operator]
    return True


def _iso_week(d: date) -> tuple[int, int]:
    iso = d.isocalendar()
    return (iso[0], iso[1])


def _daterange(since: date, until: date):
    cursor = since
    while cursor <= until:
        yield cursor
        cursor += timedelta(days=1)


def scheduled_completion_rate(
    entries: Sequence,
    since: date,
    until: date,
    schedule: str | None,
) -> float:
    """Completion rate scoped to what the schedule expects.

    daily : entry-days / calendar-days.
    dow   : entry-days-on-due-weekdays / due-weekdays.
    weekly: mean over weeks of min(distinct entry-days in week, N) / N.
    """
    if until < since:
        return 0.0
    kind, param = parse_schedule(schedule)
    dated = {e.date for e in entries}

    if kind == "weekly":
        n = param  # type: ignore[assignment]
        weeks: dict[tuple[int, int], int] = {}
        for d in _daterange(since, until):
            weeks.setdefault(_iso_week(d), 0)
        for d in dated:
            if since <= d <= until:
                weeks[_iso_week(d)] = weeks.get(_iso_week(d), 0) + 1
        if not weeks:
            return 0.0
        return sum(min(c / n, 1.0) for c in weeks.values()) / len(weeks)  # type: ignore[operator]

    due = [d for d in _daterange(since, until) if (kind != "dow" or d.weekday() in param)]  # type: ignore[operator]
    if not due:
        return 0.0
    met = sum(1 for d in due if d in dated)
    return met / len(due)


def scheduled_current_streak(
    entries: Sequence,
    today: date,
    schedule: str | None,
) -> int:
    """Streak counted in the schedule's natural unit.

    daily : consecutive calendar days with an entry, up to today.
    dow   : consecutive due weekdays with an entry (non-due days skipped).
    weekly: consecutive ISO weeks meeting the quota (current week in-progress is not
            a break — it only adds to the streak once its quota is met).
    """
    kind, param = parse_schedule(schedule)
    dated = {e.date for e in entries}
    if not dated:
        return 0

    if kind == "weekly":
        n = param  # type: ignore[assignment]
        counts: dict[tuple[int, int], int] = {}
        for d in dated:
            counts[_iso_week(d)] = counts.get(_iso_week(d), 0) + 1
        streak = 0
        cursor = today
        this_week = _iso_week(today)
        while True:
            wk = _iso_week(cursor)
            met = counts.get(wk, 0) >= n  # type: ignore[operator]
            if met:
                streak += 1
            elif wk != this_week:
                break  # a completed past week missed the quota
            # in-progress current week that hasn't met quota: don't break, keep walking back
            cursor = _week_start(cursor) - timedelta(days=1)
            if cursor < min(dated) - timedelta(days=7):
                break
        return streak

    # daily / dow: walk back through due days; first due day without an entry breaks.
    streak = 0
    cursor = today
    floor = min(dated)
    while cursor >= floor:
        if is_due(schedule, cursor):
            if cursor in dated:
                streak += 1
            else:
                break
        cursor -= timedelta(days=1)
    return streak


def scheduled_longest_streak(entries: Sequence, schedule: str | None) -> int:
    """Longest run in the schedule's natural unit (see scheduled_current_streak)."""
    kind, param = parse_schedule(schedule)
    dated = sorted({e.date for e in entries})
    if not dated:
        return 0

    if kind == "weekly":
        n = param  # type: ignore[assignment]
        counts: dict[tuple[int, int], int] = {}
        for d in dated:
            counts[_iso_week(d)] = counts.get(_iso_week(d), 0) + 1
        best = current = 0
        cursor = _week_start(dated[0])
        end = dated[-1]
        while cursor <= end:
            if counts.get(_iso_week(cursor), 0) >= n:  # type: ignore[operator]
                current += 1
                best = max(best, current)
            else:
                current = 0
            cursor += timedelta(days=7)
        return best

    best = current = 0
    for d in _daterange(dated[0], dated[-1]):
        if not is_due(schedule, d):
            continue
        if d in set(dated):
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


def _week_start(d: date) -> date:
    """Monday of d's ISO week."""
    return d - timedelta(days=d.weekday())
