"""Compact per-habit summary row for shell startup display."""
from __future__ import annotations

from datetime import date, timedelta

from rich.console import Console
from rich.text import Text

from habit_tracker.models import Entry, Habit, HabitStats
from habit_tracker.stats import intensity_bucket

# Sparkline characters mapped to intensity 0-4
_SPARK = [" ", "▁", "▃", "▆", "█"]
_COLORS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]

# Recent weeks shown in startup sparkline (4 weeks = 28 chars — compact enough for any terminal)
_SPARK_WEEKS = 4


def _sparkline(habit: Habit, entries: list[Entry], today: date) -> Text:
    entry_map: dict[date, int] = {e.date: e.count for e in entries}
    days_back = _SPARK_WEEKS * 7
    spark = Text(no_wrap=True)
    for i in range(days_back - 1, -1, -1):
        d = today - timedelta(days=i)
        count = entry_map.get(d, 0)
        level = intensity_bucket(count, habit.target)
        spark.append(_SPARK[level], style=_COLORS[level])
    return spark


def render_summary(
    habits: list[tuple[Habit, HabitStats]],
    console: Console | None = None,
    today: date | None = None,
) -> None:
    """Print one compact line per habit — safe for ~/.zshrc startup."""
    if not habits:
        return

    if today is None:
        today = date.today()

    if console is None:
        console = Console()

    for habit, stats in habits:
        spark = _sparkline(habit, stats.entries, today)
        emoji = habit.emoji or "●"
        streak = f"🔥{stats.current_streak}d" if stats.current_streak else " — "
        done_mark = "✓" if stats.done_today else "·"
        pct = f"{stats.completion_rate * 100:.0f}%"

        line = Text(no_wrap=True)
        line.append(f"{emoji} ", style="")
        line.append(f"{habit.name:<20}", style="bold")
        line.append(" ")
        line.append_text(spark)
        line.append(f"  {streak:<6}", style="yellow")
        line.append(f" {done_mark} ", style="bold green" if stats.done_today else "dim")
        line.append(f" {pct:>4}", style="dim")

        console.print(line, no_wrap=True, overflow="ellipsis")
