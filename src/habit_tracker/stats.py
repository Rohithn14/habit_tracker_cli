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


def rolling_completion(
    entries: Sequence[Entry],
    window: int = 7,
    until: date | None = None,
    days: int = 90,
    target: int | None = None,
) -> list[float]:
    """Return one rolling completion rate per day for the last `days` days.

    Each value = average fraction of the preceding `window` days completed.
    Fraction = min(count/target, 1.0) when target set; 1.0 for any entry otherwise.
    """
    if until is None:
        until = date.today()
    if target is not None and target > 0:
        dated: dict[date, float] = {e.date: min(e.count / target, 1.0) for e in entries}
    else:
        dated = {e.date: 1.0 for e in entries}
    start = until - timedelta(days=days - 1)
    results: list[float] = []
    cursor = start
    while cursor <= until:
        window_start = cursor - timedelta(days=window - 1)
        total = sum(
            dated.get(window_start + timedelta(days=i), 0.0)
            for i in range(window)
        )
        results.append(total / window)
        cursor += timedelta(days=1)
    return results


def day_of_week_bias(
    entries: Sequence[Entry],
    target: int | None = None,
) -> dict[int, float]:
    """Return average completion fraction per weekday across all history (0=Mon … 6=Sun).

    Fraction = min(count/target, 1.0) when target set; 1.0 for any entry otherwise.
    Rate = sum of daily fractions for weekday W / total occurrences of W since first entry.
    """
    if not entries:
        return {i: 0.0 for i in range(7)}
    if target is not None and target > 0:
        date_fractions: dict[date, float] = {e.date: min(e.count / target, 1.0) for e in entries}
    else:
        date_fractions = {e.date: 1.0 for e in entries}
    all_dates = {e.date for e in entries}
    since = min(all_dates)
    until = max(all_dates)
    total = [0] * 7
    frac_sum = [0.0] * 7
    cursor = since
    while cursor <= until:
        wd = cursor.weekday()
        total[wd] += 1
        frac_sum[wd] += date_fractions.get(cursor, 0.0)
        cursor += timedelta(days=1)
    return {wd: (frac_sum[wd] / total[wd] if total[wd] else 0.0) for wd in range(7)}


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
        today_count=sum(e.count for e in entries if e.date == today),
        entries=entries,
        rolling_completion=rolling_completion(entries, until=today, target=habit.target),
        day_of_week_bias=day_of_week_bias(entries, target=habit.target),
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
