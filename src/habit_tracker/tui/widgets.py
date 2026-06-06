"""Textual widgets for the habit tracker TUI."""
from __future__ import annotations

from datetime import date, timedelta

from rich.text import Text
from textual import events
from textual.message import Message
from textual.widgets import ListItem, Static

from habit_tracker.models import Entry, Habit, HabitStats
from habit_tracker.stats import intensity_bucket

# ── Shared palette (kept in sync with the registered "habit" theme) ────────────
_BLOCK = "■  "
_BLOCK_NOTE = "■• "   # trailing dot marks days that have a note
_PALETTE = ["#30363d", "#ef4444", "#f59e0b", "#22c55e", "#06b6d4"]
_SURFACE = "#161b22"   # card background — used for out-of-range cells so they blend
_DIM = "#7d8590"
_NOTE_DOT = "#a78bfa"  # violet dot matches primary theme color
_DAYS_SUNDAY = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
_DAYS_MONDAY = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
_LABEL_ROWS_SUNDAY = (1, 3, 5)
_LABEL_ROWS_MONDAY = (0, 2, 4)

# Accent colors used in markup (match theme tokens)
C_PRIMARY = "#a78bfa"
C_SECONDARY = "#22d3ee"
C_ACCENT = "#fbbf24"
C_SUCCESS = "#4ade80"
C_BG = "#0d1117"


def today_value(stats: HabitStats) -> str:
    """Short text for today's logged count, e.g. '3', '3/2', or '0'."""
    target = stats.habit.target
    if target:
        return f"{stats.today_count}/{target}"
    return str(stats.today_count)


def today_color(stats: HabitStats) -> str:
    """Green if today's goal is met, amber if partial, dim if nothing logged."""
    if stats.today_count <= 0:
        return _DIM
    target = stats.habit.target
    if target and stats.today_count < target:
        return C_ACCENT
    return C_SUCCESS


class HabitListItem(ListItem):
    """A two-line habit card in the sidebar list."""

    DEFAULT_CSS = """
    HabitListItem {
        height: 3;
        padding: 0 1;
        border-left: thick $surface;
    }
    HabitListItem.-highlighted {
        background: $boost;
        border-left: thick $accent;
    }
    HabitListItem:hover {
        background: $boost 50%;
    }
    """

    def __init__(self, habit: Habit, stats: HabitStats) -> None:
        self.habit = habit
        self.habit_stats = stats
        super().__init__(Static(self._make_label(habit, stats)))

    def _make_label(self, habit: Habit, stats: HabitStats) -> Text:
        emoji = habit.emoji or "●"
        if stats.done_today:
            badge = f"[{C_SUCCESS}]●[/]"
        elif stats.current_streak > 0:
            badge = f"[{C_ACCENT}]🔥[/]"
        else:
            badge = f"[{_DIM}]○[/]"

        top = f"{emoji}  [b]{habit.name}[/]  {badge}"

        streak = (
            f"[{C_ACCENT}]🔥 {stats.current_streak}d[/]"
            if stats.current_streak
            else f"[{_DIM}]— no streak[/]"
        )
        if stats.today_count > 0:
            tail = f"[{today_color(stats)}]· {today_value(stats)} today[/]"
        else:
            tail = f"[{_DIM}]· {stats.completion_rate * 100:.0f}%[/]"
        bottom = f"[{_DIM}]   [/]{streak}  {tail}"

        return Text.from_markup(f"{top}\n{bottom}")

    def refresh_stats(self, stats: HabitStats) -> None:
        self.habit_stats = stats
        self.query_one(Static).update(self._make_label(self.habit, stats))


class HeatmapWidget(Static):
    """Renders the contribution heatmap for one habit, with a legend.

    Posts a DaySelected message when the user clicks a cell.
    """

    class DaySelected(Message):
        def __init__(self, day: date) -> None:
            self.day = day
            super().__init__()

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        # Grid state stored so the click handler can map (x,y) → date
        self._weeks: list[list[tuple[date | None, int]]] = []
        self._habit: Habit | None = None
        self._note_dates: set[date] = set()

    def update_view(
        self,
        habit: Habit | None,
        stats: HabitStats | None,
        range_name: str,
        week_start: str = "sunday",
    ) -> None:
        if habit is None or stats is None:
            self._weeks = []
            self._habit = None
            self._note_dates = set()
            self.update("")
            return
        self._habit = habit
        self._note_dates = {e.date for e in stats.entries if e.notes}
        content = self._build_content(habit, stats, range_name, week_start)
        self.update(content)

    def _build_content(
        self, habit: Habit, stats: HabitStats, range_name: str, week_start: str = "sunday"
    ) -> Text:
        from habit_tracker.stats import range_dates

        entries = stats.entries
        since, until = range_dates(range_name)
        entry_map: dict[date, int] = {e.date: e.count for e in entries}

        if week_start == "monday":
            offset = since.weekday()
        else:
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

        self._weeks = weeks

        out = Text()

        # Month labels — scan every day so mid-week month starts are caught
        out.append("    ")
        current_month = -1
        for week in weeks:
            new_month = next(
                (d for d, _ in week if d is not None and d.month != current_month),
                None,
            )
            if new_month:
                current_month = new_month.month
                out.append(new_month.strftime("%b").ljust(3), style=f"bold {C_SECONDARY}")
            else:
                out.append("   ")
        out.append("\n")

        # Day rows
        days = _DAYS_MONDAY if week_start == "monday" else _DAYS_SUNDAY
        label_rows = _LABEL_ROWS_MONDAY if week_start == "monday" else _LABEL_ROWS_SUNDAY
        for row_idx in range(7):
            if row_idx in label_rows:
                out.append(f"{days[row_idx]} ", style=_DIM)
            else:
                out.append("    ")
            for week in weeks:
                day_date, level = week[row_idx]
                if day_date is None:
                    out.append(_BLOCK, style=_SURFACE)
                elif day_date in self._note_dates:
                    # Render the block char in palette color, dot in violet
                    out.append("■", style=_PALETTE[level])
                    out.append("•", style=_NOTE_DOT)
                    out.append(" ")
                else:
                    out.append(_BLOCK, style=_PALETTE[level])
            out.append("\n")

        # Legend
        out.append("\n    ")
        out.append("Less ", style=_DIM)
        for color in _PALETTE:
            out.append("■ ", style=color)
        out.append("More", style=_DIM)
        out.append(f"   [{_NOTE_DOT}]•[/] = note", style=_DIM)

        return out

    def on_click(self, event: events.Click) -> None:
        # Row 0 = month labels, rows 1–7 = day cells, rows 8+ = legend
        if event.y == 0 or event.y > 7 or not self._weeks:
            return
        row_idx = event.y - 1          # 0-indexed weekday slot
        week_col = (event.x - 4) // 3  # subtract 4-char prefix
        if week_col < 0 or week_col >= len(self._weeks):
            return
        day_date, _ = self._weeks[week_col][row_idx]
        if day_date is not None:
            self.post_message(self.DaySelected(day_date))


class DayDetailWidget(Static):
    """Shows stats + notes for a single selected day."""

    DEFAULT_CSS = """
    DayDetailWidget {
        height: auto;
        margin-top: 1;
        padding: 0 0;
        display: none;
        border-top: dashed $primary 30%;
    }
    DayDetailWidget.-visible {
        display: block;
    }
    """

    def show_day(self, day: date, entry: Entry | None, habit: Habit) -> None:
        self.add_class("-visible")
        self.update(self._build_content(day, entry, habit))

    def clear(self) -> None:
        self.remove_class("-visible")
        self.update("")

    def _build_content(self, day: date, entry: Entry | None, habit: Habit) -> Text:
        today = date.today()
        label = day.strftime("%A, %d %b %Y")
        is_today = day == today

        out = Text()
        day_str = f"[b {C_SECONDARY}]{label}[/]"
        if is_today:
            day_str += f" [{C_ACCENT}](today)[/]"
        out.append_text(Text.from_markup(day_str))
        out.append("\n")

        if entry is None or entry.count == 0:
            out.append_text(Text.from_markup(f"[{_DIM}]  No entry logged[/]"))
        else:
            count = entry.count
            target = habit.target
            if target:
                pct = min(count / target * 100, 100)
                bar_color = C_SUCCESS if count >= target else C_ACCENT
                out.append_text(Text.from_markup(
                    f"  [{bar_color}]Count:[/] [{bar_color}]{count}[/][{_DIM}]/{target}  ({pct:.0f}%)[/]"
                ))
            else:
                out.append_text(Text.from_markup(f"  [{C_SUCCESS}]Count:[/] [{C_SUCCESS}]{count}[/]"))

        if entry and entry.notes:
            out.append("\n")
            out.append_text(Text.from_markup(
                f"  [{C_PRIMARY}]📝[/] [{_DIM}]{entry.notes}[/]"
            ))

        return out


class MetricTile(Static):
    """A single metric card: icon, value, label."""

    DEFAULT_CSS = """
    MetricTile {
        width: 1fr;
        height: 1fr;
        margin-right: 1;
        padding: 1 0;
        background: $surface;
        border: round $primary 30%;
        content-align: center middle;
        text-align: center;
    }
    MetricTile.-last {
        margin-right: 0;
    }
    """

    def set_metric(self, icon: str, value: str, label: str, color: str) -> None:
        self.update(
            f"[{color}]{icon}[/]\n\n[b {color}]{value}[/]\n[{_DIM}]{label}[/]"
        )
