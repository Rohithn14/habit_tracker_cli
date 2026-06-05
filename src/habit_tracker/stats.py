from __future__ import annotations

from datetime import date, timedelta
from typing import Sequence

from .models import Entry, Habit, HabitStats

# GitHub palette indices 0-4 (empty → brightest green)
_PALETTE = [0, 1, 2, 3, 4]


def intensity_bucket(count: int, target: int | None) -> int:
    """Map a day's count to a 0-4 intensity level.

    0 = no entry, 1-4 = relative to target (or fixed levels if no target).
    """
    if count <= 0:
        return 0
    if target is None or target <= 0:
        return 2  # binary: done = mid-green
    ratio = count / target
    if ratio >= 1.0:
        return 4
    if ratio >= 0.75:
        return 3
    if ratio >= 0.5:
        return 2
    return 1


def current_streak(entries: Sequence[Entry], today: date | None = None) -> int:
    """Count consecutive days up to and including today with at least one entry."""
    if today is None:
        today = date.today()
    dated = {e.date for e in entries}
    streak = 0
    cursor = today
    while cursor in dated:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def longest_streak(entries: Sequence[Entry]) -> int:
    if not entries:
        return 0
    dated = sorted({e.date for e in entries})
    best = current = 1
    for i in range(1, len(dated)):
        if (dated[i] - dated[i - 1]).days == 1:
            current += 1
            best = max(best, current)
        else:
            current = 1
    return best


def completion_rate(
    entries: Sequence[Entry],
    since: date,
    until: date,
) -> float:
    total_days = (until - since).days + 1
    if total_days <= 0:
        return 0.0
    dated = {e.date for e in entries if since <= e.date <= until}
    return len(dated) / total_days


def build_stats(
    habit: Habit,
    entries: list[Entry],
    today: date | None = None,
    since: date | None = None,
) -> HabitStats:
    if today is None:
        today = date.today()
    if since is None:
        since = today.replace(month=1, day=1)
    return HabitStats(
        habit=habit,
        current_streak=current_streak(entries, today),
        longest_streak=longest_streak(entries),
        completion_rate=completion_rate(entries, since, today),
        total_completions=len({e.date for e in entries}),
        done_today=any(e.date == today for e in entries),
        entries=entries,
    )


def range_dates(range_name: str, today: date | None = None) -> tuple[date, date]:
    """Return (since, until) for a named range."""
    if today is None:
        today = date.today()
    if range_name == "month":
        since = today.replace(day=1)
    elif range_name == "quarter":
        quarter_start_month = ((today.month - 1) // 3) * 3 + 1
        since = today.replace(month=quarter_start_month, day=1)
    else:  # year (default)
        since = today.replace(month=1, day=1)
    return since, today
