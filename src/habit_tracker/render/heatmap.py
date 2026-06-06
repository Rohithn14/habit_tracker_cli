"""GitHub-style heatmap rendered with Rich."""
from __future__ import annotations

from datetime import date, timedelta

from rich.console import Console
from rich.style import Style
from rich.text import Text

from habit_tracker.models import Entry, Habit
from habit_tracker.stats import intensity_bucket, range_dates

_PALETTE = [
    "#30363d",  # 0 – empty  (visible dark gray)
    "#ef4444",  # 1 – low    (red)
    "#f59e0b",  # 2 – partial (amber)
    "#22c55e",  # 3 – good   (green)
    "#06b6d4",  # 4 – max    (cyan)
]

_BLOCK = "■  "  # 3-char cell so 3-letter month labels align
_DAYS_SUNDAY = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
_DAYS_MONDAY = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
# Rows to label (Mon, Wed, Fri) differ by start day
_LABEL_ROWS_SUNDAY = (1, 3, 5)  # Mon, Wed, Fri in Sun-start grid
_LABEL_ROWS_MONDAY = (0, 2, 4)  # Mon, Wed, Fri in Mon-start grid


def _week_start_offset(first_day: date, week_start: str = "sunday") -> int:
    """Number of days to pad before first_day so the grid starts on the chosen weekday."""
    if week_start == "monday":
        return first_day.weekday()          # Mon=0 → no pad; Sun=6 → 6 pad
    return (first_day.weekday() + 1) % 7   # Mon=1; Sun=0


def render_heatmap(
    habit: Habit,
    entries: list[Entry],
    range_name: str = "year",
    console: Console | None = None,
    week_start: str = "sunday",
) -> None:
    if console is None:
        console = Console()

    since, until = range_dates(range_name)
    entry_map: dict[date, int] = {e.date: e.count for e in entries}

    offset = _week_start_offset(since, week_start)
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
        # Scan all days so months starting mid-week (non-Sunday) are caught
        new_month = next(
            (d for d, _ in week if d is not None and d.month != current_month),
            None,
        )
        if new_month:
            current_month = new_month.month
            month_label_row.append(new_month.strftime("%b").ljust(3), style=Style(color="bright_white", bold=True))
        else:
            month_label_row.append("   ")
    console.print(month_label_row)

    # ── Day rows ──────────────────────────────────────────────────────────────
    days = _DAYS_MONDAY if week_start == "monday" else _DAYS_SUNDAY
    label_rows = _LABEL_ROWS_MONDAY if week_start == "monday" else _LABEL_ROWS_SUNDAY
    for row_idx in range(7):
        day_name = days[row_idx]
        if row_idx in label_rows:
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
    week_start: str = "sunday",
) -> Text:
    """Return the heatmap as a single Rich Text object (for embedding in TUI)."""
    from io import StringIO
    from rich.console import Console as _Console

    buf = StringIO()
    c = _Console(file=buf, highlight=False, markup=False, width=200)
    render_heatmap(habit, entries, range_name, console=c, week_start=week_start)
    # Re-build as plain Text — for TUI use the widget approach instead
    return Text(buf.getvalue())
