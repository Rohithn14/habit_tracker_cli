"""Textual widgets for the habit tracker TUI."""
from __future__ import annotations

from datetime import date, timedelta

from rich.text import Text
from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import ListItem, ListView, Static

from habit_tracker.models import Habit, HabitStats
from habit_tracker.stats import intensity_bucket

_BLOCK = "■  "
_PALETTE = ["#30363d", "#ef4444", "#f59e0b", "#22c55e", "#06b6d4"]
_DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
_SPARK = [" ", "▁", "▃", "▆", "█"]


class HabitListItem(ListItem):
    """A single row in the habit sidebar list."""

    DEFAULT_CSS = """
    HabitListItem {
        height: 1;
        padding: 0 1;
    }
    HabitListItem:focus, HabitListItem.-highlighted {
        background: $accent 20%;
    }
    """

    def __init__(self, habit: Habit, stats: HabitStats) -> None:
        self.habit = habit
        self.habit_stats = stats
        label = self._make_label(habit, stats)
        super().__init__(Static(label))

    def _make_label(self, habit: Habit, stats: HabitStats) -> Text:
        text = Text(no_wrap=True, overflow="ellipsis")
        emoji = habit.emoji or "●"
        text.append(f"{emoji} ", style="")
        text.append(f"{habit.name}", style="bold")
        if stats.done_today:
            text.append(" ✓", style="bold green")
        elif stats.current_streak > 0:
            text.append(f" 🔥{stats.current_streak}", style="yellow")
        return text

    def refresh_stats(self, stats: HabitStats) -> None:
        self.habit_stats = stats
        label = self._make_label(self.habit, stats)
        self.query_one(Static).update(label)


class HeatmapWidget(Static):
    """Renders a GitHub-style heatmap for one habit."""

    DEFAULT_CSS = """
    HeatmapWidget {
        padding: 1 2;
    }
    """

    habit: reactive[Habit | None] = reactive(None)
    stats: reactive[HabitStats | None] = reactive(None)
    range_name: reactive[str] = reactive("year")

    def watch_habit(self, _: Habit | None) -> None:
        self._refresh_content()

    def watch_stats(self, _: HabitStats | None) -> None:
        self._refresh_content()

    def watch_range_name(self, _: str) -> None:
        self._refresh_content()

    def _refresh_content(self) -> None:
        if self.habit is None or self.stats is None:
            self.update("")
            return
        self.update(self._build_content())

    def _build_content(self) -> Text:
        from habit_tracker.stats import range_dates

        habit = self.habit
        entries = self.stats.entries if self.stats else []
        since, until = range_dates(self.range_name)

        entry_map: dict[date, int] = {e.date: e.count for e in entries}

        # Align grid start to Sunday
        offset = (since.weekday() + 1) % 7
        grid_start = since - timedelta(days=offset)

        weeks: list[list[tuple[date | None, int]]] = []
        cursor = grid_start
        while cursor <= until:
            week: list[tuple[date | None, int]] = []
            for _ in range(7):
                if cursor < since or cursor > until:
                    week.append((None, 0))
                else:
                    count = entry_map.get(cursor, 0)
                    week.append((cursor, intensity_bucket(count, habit.target)))
                cursor += timedelta(days=1)
            weeks.append(week)

        out = Text()

        # Month labels — scan all days in week so months starting mid-week (non-Sunday) are caught
        out.append("    ")
        current_month = -1
        for week in weeks:
            new_month = next(
                (d for d, _ in week if d is not None and d.month != current_month),
                None,
            )
            if new_month:
                current_month = new_month.month
                out.append(new_month.strftime("%b").ljust(3), style="bold white")
            else:
                out.append("   ")
        out.append("\n")

        for row_idx in range(7):
            if row_idx in (1, 3, 5):
                out.append(f"{_DAYS[row_idx][:3]} ", style="bright_black")
            else:
                out.append("    ", style="bright_black")
            for week in weeks:
                day_date, level = week[row_idx]
                color = "#0d1117" if day_date is None else _PALETTE[level]
                out.append(_BLOCK, style=color)
            out.append("\n")

        return out


class StatsWidget(Static):
    """Renders streak + stats for the selected habit."""

    DEFAULT_CSS = """
    StatsWidget {
        padding: 1 2;
        border-top: solid $accent 30%;
    }
    """

    stats: reactive[HabitStats | None] = reactive(None)

    def watch_stats(self, stats: HabitStats | None) -> None:
        if stats is None:
            self.update("")
            return
        self.update(self._build_content(stats))

    def _build_content(self, stats: HabitStats) -> Text:
        h = stats.habit
        title = f"{h.emoji} {h.name}" if h.emoji else h.name
        done_str = "[bold green]✓ Done[/bold green]" if stats.done_today else "[dim]· Pending[/dim]"

        lines = [
            f"[bold]{title}[/bold]",
            "",
            f"[dim]Today[/dim]          {done_str}",
            f"[dim]Current streak[/dim]  [bold yellow]{stats.current_streak} days[/bold yellow]",
            f"[dim]Longest streak[/dim]  {stats.longest_streak} days",
            f"[dim]Completion[/dim]      {stats.completion_rate * 100:.1f}%",
            f"[dim]Total logged[/dim]    {stats.total_completions} days",
        ]
        if h.target:
            lines.append(f"[dim]Daily target[/dim]    {h.target}")

        lines += [
            "",
            "[dim]Keys: [bold]d[/bold]=done  [bold]c[/bold]=log count  [bold]u[/bold]=undo  [bold]a[/bold]=add  [bold]x[/bold]=delete  [bold]1/2/3[/bold]=range  [bold]q[/bold]=quit[/dim]",
        ]
        return Text.from_markup("\n".join(lines))
