"""Rich stats panel shown below/beside the heatmap."""
from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from habit_tracker.models import HabitStats

_WEEKDAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
_BAR_WIDTH = 12


def render_stats_panel(
    stats: HabitStats,
    console: Console | None = None,
    range_label: str | None = None,
) -> None:
    if console is None:
        console = Console()

    grid = Table.grid(padding=(0, 2))
    grid.add_column(justify="left")
    grid.add_column(justify="right")

    def row(label: str, value: str, style: str = "") -> None:
        grid.add_row(
            Text(label, style="dim"),
            Text(value, style=style or "bright_white"),
        )

    # Streaks and totals are all-time; completion is scoped to the selected range.
    span = f" ({range_label})" if range_label else ""
    row("Current streak (all-time)", f"{stats.current_streak} days", "bold yellow")
    row("Longest streak (all-time)", f"{stats.longest_streak} days")
    row(f"Completion{span}", f"{stats.completion_rate * 100:.1f}%")
    row("Total completions (all-time)", str(stats.total_completions))
    today_val = "✓ Done" if stats.done_today else "· Pending"
    today_style = "bold green" if stats.done_today else "dim"
    row("Today", today_val, today_style)

    target = stats.habit.target
    if target:
        row("Daily target", str(target))

    title = f"{stats.habit.emoji} {stats.habit.name}" if stats.habit.emoji else stats.habit.name
    console.print(Panel(grid, title=f"[bold]{title}[/bold]", expand=False))

    # Day-of-week breakdown
    if stats.day_of_week_bias:
        dow_grid = Table.grid(padding=(0, 1))
        dow_grid.add_column(justify="left", width=4)
        dow_grid.add_column(justify="left", width=_BAR_WIDTH)
        dow_grid.add_column(justify="right", width=5)
        for wd in range(7):
            rate = stats.day_of_week_bias.get(wd, 0.0)
            filled = round(rate * _BAR_WIDTH)
            empty = _BAR_WIDTH - filled
            if rate >= 0.7:
                bar_color = "green"
            elif rate >= 0.4:
                bar_color = "yellow"
            else:
                bar_color = "bright_black"
            bar = Text("█" * filled, style=bar_color) + Text("░" * empty, style="bright_black")
            dow_grid.add_row(
                Text(_WEEKDAY_NAMES[wd], style="dim"),
                bar,
                Text(f"{rate:.0%}", style=bar_color),
            )
        console.print(Panel(dow_grid, title="[bold]By Day of Week[/bold]", expand=False))
