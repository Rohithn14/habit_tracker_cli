"""Rich stats panel shown below/beside the heatmap."""
from __future__ import annotations

from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from habit_tracker.models import HabitStats


def render_stats_panel(stats: HabitStats, console: Console | None = None) -> None:
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

    row("Current streak", f"{stats.current_streak} days", "bold yellow")
    row("Longest streak", f"{stats.longest_streak} days")
    row("Completion", f"{stats.completion_rate * 100:.1f}%")
    row("Total completions", str(stats.total_completions))
    today_val = "✓ Done" if stats.done_today else "· Pending"
    today_style = "bold green" if stats.done_today else "dim"
    row("Today", today_val, today_style)

    target = stats.habit.target
    if target:
        row("Daily target", str(target))

    title = f"{stats.habit.emoji} {stats.habit.name}" if stats.habit.emoji else stats.habit.name
    console.print(Panel(grid, title=f"[bold]{title}[/bold]", expand=False))
