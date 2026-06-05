"""Compact per-habit summary row for shell startup display."""
from __future__ import annotations

from datetime import date, timedelta

from rich.console import Console
from rich.table import Table
from rich.text import Text

from habit_tracker.models import Entry, Habit, HabitStats
from habit_tracker.stats import intensity_bucket

# Sparkline characters mapped to intensity 0-4
_SPARK = [" ", "▁", "▃", "▆", "█"]

# Recent weeks shown in startup sparkline
_SPARK_WEEKS = 16


def _sparkline(habit: Habit, entries: list[Entry], today: date) -> Text:
    entry_map: dict[date, int] = {e.date: e.count for e in entries}
    days_back = _SPARK_WEEKS * 7
    spark = Text()
    for i in range(days_back - 1, -1, -1):
        d = today - timedelta(days=i)
        count = entry_map.get(d, 0)
        level = intensity_bucket(count, habit.target)
        # Color matches heatmap palette (simplified for one-liner)
        colors = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
        spark.append(_SPARK[level], style=colors[level])
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

    table = Table.grid(padding=(0, 1))
    table.add_column(justify="left", min_width=2)              # emoji
    table.add_column(justify="left", min_width=18)             # name
    table.add_column(justify="left", no_wrap=True, min_width=_SPARK_WEEKS * 7)  # sparkline
    table.add_column(justify="right", min_width=6)             # streak
    table.add_column(justify="center", min_width=3)            # today
    table.add_column(justify="right", min_width=5)             # pct

    for habit, stats in habits:
        spark = _sparkline(habit, stats.entries, today)
        emoji = habit.emoji or "●"
        streak_txt = Text(f"🔥{stats.current_streak}d", style="yellow")
        today_mark = Text("✓", style="bold green") if stats.done_today else Text("·", style="dim")
        pct_txt = Text(f"{stats.completion_rate * 100:.0f}%", style="dim")
        name_txt = Text(habit.name, style="bold")
        table.add_row(emoji, name_txt, spark, streak_txt, today_mark, pct_txt)

    console.print(table)
