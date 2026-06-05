"""Interactive Textual TUI for the habit tracker."""
from __future__ import annotations

from datetime import date

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header, Input, Label, ListView

from habit_tracker.models import Habit, HabitStats
from habit_tracker.storage import (
    create_habit,
    delete_habit,
    get_entries,
    list_habits,
    log_entry,
    remove_entry,
)
from habit_tracker.stats import build_stats, range_dates
from habit_tracker.tui.widgets import HabitListItem, HeatmapWidget, StatsWidget

_RANGES = ["year", "quarter", "month"]


class HabitApp(App):
    """Habit tracker interactive TUI."""

    CSS = """
    Screen {
        background: #0d1117;
    }
    #sidebar {
        width: 28;
        border-right: solid $accent 30%;
        padding: 0;
    }
    #sidebar-title {
        background: $accent 20%;
        padding: 0 1;
        height: 1;
        content-align: center middle;
        text-style: bold;
        color: $text;
    }
    #main {
        width: 1fr;
    }
    #range-label {
        padding: 0 2;
        color: $text-muted;
        height: 1;
    }
    ListView {
        background: transparent;
        border: none;
        padding: 0;
    }
    HeatmapWidget {
        height: 12;
    }
    StatsWidget {
        height: 1fr;
    }
    #add-bar {
        height: 3;
        border-top: solid $accent 30%;
        padding: 0 2;
        display: none;
    }
    #add-bar.visible {
        display: block;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("d", "mark_done", "Done today"),
        Binding("c", "log_count", "Log count"),
        Binding("u", "mark_undo", "Undo today"),
        Binding("a", "add_habit", "Add habit"),
        Binding("x", "delete_habit", "Delete"),
        Binding("1", "set_range_year", "Year"),
        Binding("2", "set_range_quarter", "Quarter"),
        Binding("3", "set_range_month", "Month"),
        Binding("j,down", "cursor_down", "Down", show=False),
        Binding("k,up", "cursor_up", "Up", show=False),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._range = "year"
        self._habits: list[Habit] = []
        self._stats: dict[int, HabitStats] = {}

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal():
            with Vertical(id="sidebar"):
                yield Label("  Habits", id="sidebar-title")
                yield ListView(id="habit-list")
            with Vertical(id="main"):
                yield Label(self._range_label(), id="range-label")
                yield HeatmapWidget(id="heatmap")
                yield StatsWidget(id="stats")
        yield Input(placeholder="Habit name (Enter to confirm, Esc to cancel)", id="add-input")
        yield Input(placeholder="Count for today (Enter to confirm, Esc to cancel)", id="count-input")
        yield Footer()

    def on_mount(self) -> None:
        self._load_habits()
        self.query_one("#add-input", Input).display = False
        self.query_one("#count-input", Input).display = False

    def _range_label(self) -> str:
        return f"  Range: [bold]{self._range}[/bold]  (1=year  2=quarter  3=month)"

    def _load_habits(self) -> None:
        self._habits = list_habits()
        today = date.today()
        self._stats = {}
        for h in self._habits:
            entries = get_entries(h.id)
            since, _ = range_dates(self._range)
            self._stats[h.id] = build_stats(h, entries, today=today, since=since)

        lv = self.query_one("#habit-list", ListView)
        lv.clear()
        for h in self._habits:
            lv.append(HabitListItem(h, self._stats[h.id]))

        # Select first item
        if self._habits:
            lv.index = 0
            self._update_detail(self._habits[0])

    def _update_detail(self, habit: Habit) -> None:
        stats = self._stats.get(habit.id)
        heatmap = self.query_one("#heatmap", HeatmapWidget)
        stats_w = self.query_one("#stats", StatsWidget)
        entries = get_entries(habit.id)
        since, until = range_dates(self._range)
        range_entries = [e for e in entries if since <= e.date <= until]
        heatmap.habit = habit
        # Pass full entries for streak but range entries for display
        # Build a fresh stats with range entries for heatmap display
        from habit_tracker.stats import build_stats as _bs
        today = date.today()
        full_stats = _bs(habit, entries, today=today, since=since)
        heatmap.stats = full_stats  # uses .entries for the map lookup
        heatmap.range_name = self._range
        stats_w.stats = full_stats

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if event.item is None:
            return
        if isinstance(event.item, HabitListItem):
            self._update_detail(event.item.habit)

    def _selected_habit(self) -> Habit | None:
        lv = self.query_one("#habit-list", ListView)
        item = lv.highlighted_child
        if isinstance(item, HabitListItem):
            return item.habit
        return None

    def action_mark_done(self) -> None:
        h = self._selected_habit()
        if h is None:
            return
        log_entry(h.id, date.today())
        self._reload_habit(h)
        self.notify(f"✓ {h.name} logged for today")

    def action_mark_undo(self) -> None:
        h = self._selected_habit()
        if h is None:
            return
        removed = remove_entry(h.id, date.today())
        if removed:
            self._reload_habit(h)
            self.notify(f"↩ Removed today's entry for {h.name}")
        else:
            self.notify(f"No entry for today ({h.name})", severity="warning")

    def _reload_habit(self, h: Habit) -> None:
        entries = get_entries(h.id)
        since, _ = range_dates(self._range)
        self._stats[h.id] = build_stats(h, entries, today=date.today(), since=since)
        # Refresh the list item
        lv = self.query_one("#habit-list", ListView)
        for item in lv.query(HabitListItem):
            if item.habit.id == h.id:
                item.refresh_stats(self._stats[h.id])
                break
        self._update_detail(h)

    def action_add_habit(self) -> None:
        inp = self.query_one("#add-input", Input)
        inp.display = True
        inp.focus()

    def action_log_count(self) -> None:
        h = self._selected_habit()
        if h is None:
            return
        inp = self.query_one("#count-input", Input)
        inp.display = True
        inp.focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "count-input":
            self._handle_count_submitted(event.value.strip())
        else:
            self._handle_add_submitted(event.value.strip())

    def _handle_add_submitted(self, name: str) -> None:
        inp = self.query_one("#add-input", Input)
        inp.display = False
        inp.value = ""
        if name:
            from habit_tracker.storage import get_habit
            if get_habit(name) is None:
                create_habit(name)
                self.notify(f"Created habit: {name}")
            else:
                self.notify(f"Habit '{name}' already exists", severity="warning")
            self._load_habits()
        self.query_one("#habit-list", ListView).focus()

    def _handle_count_submitted(self, raw: str) -> None:
        inp = self.query_one("#count-input", Input)
        inp.display = False
        inp.value = ""
        h = self._selected_habit()
        if h and raw:
            try:
                n = int(raw)
            except ValueError:
                self.notify("Enter a whole number", severity="warning")
                self.query_one("#habit-list", ListView).focus()
                return
            if n <= 0:
                self.notify("Count must be > 0", severity="warning")
                self.query_one("#habit-list", ListView).focus()
                return
            log_entry(h.id, date.today(), count=n)
            self._reload_habit(h)
            label = f"{h.emoji} {h.name}" if h.emoji else h.name
            self.notify(f"✓ {label} logged ×{n} for today")
        self.query_one("#habit-list", ListView).focus()

    def on_input_key(self, event) -> None:  # type: ignore[override]
        if event.key == "escape":
            for inp_id in ("#add-input", "#count-input"):
                inp = self.query_one(inp_id, Input)
                inp.display = False
                inp.value = ""
            self.query_one("#habit-list", ListView).focus()

    def action_delete_habit(self) -> None:
        h = self._selected_habit()
        if h is None:
            return
        delete_habit(h.name)
        self.notify(f"Deleted: {h.name}", severity="warning")
        self._load_habits()

    def action_set_range_year(self) -> None:
        self._set_range("year")

    def action_set_range_quarter(self) -> None:
        self._set_range("quarter")

    def action_set_range_month(self) -> None:
        self._set_range("month")

    def _set_range(self, r: str) -> None:
        self._range = r
        self.query_one("#range-label", Label).update(self._range_label())
        h = self._selected_habit()
        if h:
            self._reload_habit(h)

    def action_cursor_down(self) -> None:
        self.query_one("#habit-list", ListView).action_cursor_down()

    def action_cursor_up(self) -> None:
        self.query_one("#habit-list", ListView).action_cursor_up()
