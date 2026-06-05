"""GitHub-style heatmap rendered with Rich."""
from __future__ import annotations

from datetime import date, timedelta

from rich.console import Console
from rich.style import Style
from rich.text import Text

from habit_tracker.models import Entry, Habit
from habit_tracker.stats import intensity_bucket, range_dates

_PALETTE = [
    "#161b22",  # 0 – empty
    "#ef4444",  # 1 – low    (red)
    "#f59e0b",  # 2 – partial (amber)
    "#22c55e",  # 3 – good   (green)
    "#06b6d4",  # 4 – max    (cyan)
]

_BLOCK = "■  "  # 3-char cell so 3-letter month labels align
_DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]


def _week_start_offset(first_day: date) -> int:
    """Weekday index of first_day where Sunday=0."""
    return (first_day.weekday() + 1) % 7


def render_heatmap(
    habit: Habit,
    entries: list[Entry],
    range_name: str = "year",
    console: Console | None = None,
) -> None:
    if console is None:
        console = Console()

    since, until = range_dates(range_name)
    entry_map: dict[date, int] = {e.date: e.count for e in entries}

    # Build a grid: rows = weekdays (Sun=0), cols = ISO weeks
    # Align so the grid always starts on a Sunday column.
    # Find the Sunday on or before `since`.
    offset = _week_start_offset(since)
    grid_start = since - timedelta(days=offset)
    grid_end = until

    # Collect all weeks
    weeks: list[list[tuple[date | None, int]]] = []  # weeks[col][row]
    cursor = grid_start
    while cursor <= grid_end:
        week: list[tuple[date | None, int]] = []
        for _ in range(7):
            if cursor < since or cursor > grid_end:
                week.append((None, 0))
            else:
                count = entry_map.get(cursor, 0)
                week.append((cursor, intensity_bucket(count, habit.target)))
            cursor += timedelta(days=1)
        weeks.append(week)

    # ── Month labels row ──────────────────────────────────────────────────────
    month_label_row = Text()
    month_label_row.append("    ")  # 4-char prefix matching day-label width
    current_month = -1
    for week in weeks:
        first_valid = next((d for d, _ in week if d is not None), None)
        if first_valid and first_valid.month != current_month:
            current_month = first_valid.month
            label = first_valid.strftime("%b")
            month_label_row.append(label.ljust(3), style=Style(color="bright_white", bold=True))
        else:
            month_label_row.append("   ")
    console.print(month_label_row)

    # ── Day rows ──────────────────────────────────────────────────────────────
    for row_idx in range(7):
        day_name = _DAYS[row_idx]
        # Only print label for Mon, Wed, Fri to match GitHub style
        if row_idx in (1, 3, 5):
            prefix = f"{day_name[:3]} "
        else:
            prefix = "    "

        line = Text(prefix, style=Style(color="bright_black"))
        for week in weeks:
            day_date, level = week[row_idx]
            if day_date is None:
                line.append(_BLOCK, style=Style(color="#0d1117"))  # hidden
            else:
                color = _PALETTE[level]
                line.append(_BLOCK, style=Style(color=color))
        console.print(line)

    console.print()  # trailing newline


def render_heatmap_text(
    habit: Habit,
    entries: list[Entry],
    range_name: str = "year",
) -> Text:
    """Return the heatmap as a single Rich Text object (for embedding in TUI)."""
    from io import StringIO
    from rich.console import Console as _Console

    buf = StringIO()
    c = _Console(file=buf, highlight=False, markup=False, width=200)
    render_heatmap(habit, entries, range_name, console=c)
    # Re-build as plain Text — for TUI use the widget approach instead
    return Text(buf.getvalue())
