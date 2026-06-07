"""Interactive Textual TUI for the habit tracker."""
from __future__ import annotations

from datetime import date

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.theme import Theme
from textual.widgets import Footer, Header, Input, ListView, Static

from habit_tracker.models import Habit, HabitStats
from habit_tracker.storage import (
    create_habit,
    delete_habit,
    get_entries,
    list_habits,
    log_entry,
    remove_entry,
    set_entry_note,
)
from habit_tracker.stats import build_stats, range_dates
from habit_tracker.tui.widgets import (
    C_ACCENT,
    C_BG,
    C_SUCCESS,
    DayDetailWidget,
    DayOfWeekWidget,
    HabitListItem,
    HeatmapWidget,
    MetricTile,
    TrendChartWidget,
    today_color,
    today_value,
)
from habit_tracker.tui.commands import HabitCommands
from habit_tracker.tui.screens import ConfirmScreen, EditHabitScreen, SettingsScreen

_RANGES = ["year", "quarter", "month"]
_DIM = "#7d8590"

HABIT_THEME = Theme(
    name="habit",
    primary="#a78bfa",      # violet
    secondary="#22d3ee",    # cyan
    accent="#fbbf24",       # amber
    foreground="#e6edf3",
    background="#0d1117",
    surface="#161b22",
    panel="#1c2128",
    success="#4ade80",
    warning="#fbbf24",
    error="#ef4444",
    dark=True,
    variables={
        "boost": "#2d333b",
        "block-cursor-foreground": "#0d1117",
        "footer-key-foreground": "#a78bfa",
    },
)


class HabitApp(App):
    """Habit tracker interactive TUI."""

    COMMANDS = {HabitCommands}

    CSS = """
    Screen {
        background: $background;
        layers: base overlay;
    }

    #body {
        padding: 1 1 0 1;
        layer: base;
    }

    /* ── Sidebar ─────────────────────────────────────────── */
    #sidebar {
        width: 34;
        height: 1fr;
        margin-right: 1;
    }
    #habit-list {
        height: 1fr;
        background: $surface;
        border: round $primary 60%;
        border-title-color: $primary;
        border-title-style: bold;
        padding: 1 0;
    }
    ListView:focus {
        border: round $primary;
    }

    /* ── Content ─────────────────────────────────────────── */
    #content {
        width: 1fr;
        height: 1fr;
        layers: base overlay;
    }
    #topbar {
        height: 3;
        margin-bottom: 1;
    }
    #habit-title {
        width: 1fr;
        height: 3;
        content-align: left middle;
        padding: 0 2;
        background: $surface;
        border: round $primary 60%;
    }
    #range-pills {
        width: auto;
        min-width: 34;
        height: 3;
        content-align: center middle;
        text-align: center;
        padding: 0 2;
        margin-left: 1;
        background: $surface;
        border: round $secondary 50%;
    }

    #heatmap-card {
        height: 1fr;
        background: $surface;
        border: round $secondary 50%;
        border-title-color: $secondary;
        border-title-style: bold;
        padding: 1 2;
        margin-bottom: 1;
    }
    HeatmapWidget {
        height: auto;
    }

    /* ── Day detail overlay (floats over content, no layout cost) ── */
    DayDetailWidget {
        layer: overlay;
        dock: right;
        width: 46;
        height: auto;
        max-height: 16;
        background: $surface;
        border: round $primary;
        border-title-color: $primary;
        border-title-style: bold;
        padding: 1 2;
        display: none;
        overflow-y: auto;
    }
    DayDetailWidget.-visible {
        display: block;
    }

    /* ── Analytics row ───────────────────────────────────── */
    #analytics-row {
        height: 11;
        margin-bottom: 1;
    }
    #trend-card {
        width: 1fr;
        height: 1fr;
        background: $surface;
        border: round $secondary 50%;
        border-title-color: $secondary;
        border-title-style: bold;
        padding: 1 2;
        margin-right: 1;
    }
    TrendChartWidget {
        height: 1fr;
    }
    #dow-card {
        width: 34;
        height: 1fr;
        background: $surface;
        border: round $accent 30%;
        border-title-color: $accent;
        border-title-style: bold;
        padding: 1 2;
    }
    DayOfWeekWidget {
        height: auto;
    }

    #metrics {
        height: 9;
    }

    /* ── Input overlay (scoped to the bottom overlay inputs only, so it
          doesn't hide Inputs inside modal screens) ──────────── */
    #add-input, #count-input, #note-input, #search-input {
        layer: overlay;
        dock: bottom;
        margin: 0 1 1 1;
        border: round $accent;
        background: $panel;
        display: none;
    }
    #add-input.-active, #count-input.-active, #note-input.-active, #search-input.-active {
        display: block;
    }

    /* ── Command palette (Ctrl+P) — modernized ───────────── */
    CommandPalette {
        background: $background 70%;
    }
    CommandPalette > Vertical {
        margin-top: 6;
        width: 76;
        max-width: 90%;
        border: round $primary;
        background: $surface;
        &:dark { background: $surface; }
    }
    CommandPalette #--input {
        height: auto;
        border: none;
        border-bottom: solid $primary 30%;
        padding: 0 1;
    }
    CommandPalette #--input.--list-visible {
        border-bottom: solid $primary 30%;
    }
    SearchIcon {
        color: $accent;
    }
    CommandInput, CommandInput:focus {
        background: transparent;
        color: $foreground;
    }
    CommandList {
        border: none;
        background: transparent;
        padding: 1 0;
    }
    CommandList:focus {
        border: none;
    }
    CommandList > .option-list--option {
        padding: 0 2;
        color: $foreground;
    }
    CommandList > .option-list--option-highlighted {
        color: $foreground;
        background: $primary 30%;
        text-style: bold;
    }
    CommandPalette > .command-palette--highlight {
        color: $accent;
        text-style: bold;
    }
    CommandPalette > .command-palette--help-text {
        color: $text-muted;
        text-style: dim not bold;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("d", "mark_done", "Done"),
        Binding("c", "log_count", "Count"),
        Binding("u", "mark_undo", "Undo"),
        Binding("n", "add_note", "Note"),
        Binding("slash", "search", "Search", show=False),
        Binding("a", "add_habit", "Add"),
        Binding("e", "edit_habit", "Edit"),
        Binding("x", "delete_habit", "Delete"),
        Binding("comma", "open_settings", "Settings"),
        Binding("1", "set_range_year", "Year"),
        Binding("2", "set_range_quarter", "Quarter"),
        Binding("3", "set_range_month", "Month"),
        Binding("j,down", "cursor_down", "Down", show=False),
        Binding("k,up", "cursor_up", "Up", show=False),
        Binding("escape", "cancel_input", "Cancel", show=False, priority=True),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._range = "year"
        self._week_start = "sunday"
        self._compact = False
        self._habits: list[Habit] = []
        self._filtered_habits: list[Habit] = []
        self._stats: dict[int, HabitStats] = {}
        # The heatmap cell currently selected for backfill logging (None = act on today).
        self._focused_day: date | None = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="body"):
            with Vertical(id="sidebar"):
                yield ListView(id="habit-list")
            with Vertical(id="content"):
                with Horizontal(id="topbar"):
                    yield Static(id="habit-title")
                    yield Static(self._range_pills(), id="range-pills")
                with Vertical(id="heatmap-card"):
                    yield HeatmapWidget(id="heatmap")
                with Horizontal(id="analytics-row"):
                    with Vertical(id="trend-card"):
                        yield TrendChartWidget(id="trend-chart")
                    with Vertical(id="dow-card"):
                        yield DayOfWeekWidget(id="dow-chart")
                with Horizontal(id="metrics"):
                    yield MetricTile(id="m-today")
                    yield MetricTile(id="m-streak")
                    yield MetricTile(id="m-best")
                    yield MetricTile(id="m-rate", classes="-last")
                yield DayDetailWidget(id="day-detail")
        yield Input(placeholder="New habit name — Enter to add, Esc to cancel", id="add-input")
        yield Input(placeholder="Count for today — Enter to log, Esc to cancel", id="count-input")
        yield Input(placeholder="Note for today — Enter to save, Esc to cancel", id="note-input")
        yield Input(placeholder="Filter habits (try cat:fitness) — Esc to clear", id="search-input")
        yield Footer()

    def on_mount(self) -> None:
        from habit_tracker.config import load_config
        cfg = load_config()
        self._week_start = cfg.get("week_start", "sunday")
        self._range = cfg.get("default_range", "year")
        self.register_theme(HABIT_THEME)
        self.theme = "habit"
        self.title = "Habit Tracker"
        self.sub_title = "contribution heatmaps in your terminal"
        self.query_one("#habit-list", ListView).border_title = "✦  Habits"
        self.query_one("#heatmap-card", Vertical).border_title = "  Activity  "
        self.query_one("#trend-card", Vertical).border_title = "  Trend  "
        self.query_one("#dow-card", Vertical).border_title = "  By Day  "
        self._load_habits()
        self.query_one("#habit-list", ListView).focus()

    # ── Range selector ────────────────────────────────────────────────────────
    def _range_pills(self) -> str:
        pills = []
        for n, r in enumerate(_RANGES, start=1):
            label = r.capitalize()
            if r == self._range:
                pills.append(f"[b {C_BG} on {C_ACCENT}] {n} {label} [/]")
            else:
                pills.append(f"[{_DIM}] {n} {label} [/]")
        return " ".join(pills)

    # ── Data loading / detail rendering ───────────────────────────────────────
    def _load_habits(self) -> None:
        self._habits = list_habits()
        self._filtered_habits = self._habits
        today = date.today()
        since, _ = range_dates(self._range)
        self._stats = {
            h.id: build_stats(h, get_entries(h.id), today=today, since=since)
            for h in self._habits
        }
        self._rebuild_list(self._filtered_habits)

    def _rebuild_list(self, habits: list[Habit]) -> None:
        lv = self.query_one("#habit-list", ListView)
        lv.clear()
        for h in habits:
            lv.append(HabitListItem(h, self._stats[h.id], compact=self._compact))
        if habits:
            lv.index = 0
            self._update_detail(habits[0])
        else:
            self.query_one("#habit-title", Static).update(
                f"[{_DIM}]No habits yet — press [b]a[/b] to add one[/]"
            )

    def _update_detail(self, habit: Habit) -> None:
        self.query_one("#day-detail", DayDetailWidget).clear()
        today = date.today()
        since, _ = range_dates(self._range)
        stats = build_stats(habit, get_entries(habit.id), today=today, since=since)

        # Title bar
        emoji = habit.emoji or "●"
        if stats.today_count > 0:
            tcol = today_color(stats)
            badge = f"[b {tcol}]●  {today_value(stats)} today[/]"
        else:
            badge = f"[{_DIM}]○  Not done today[/]"
        self.query_one("#habit-title", Static).update(f"{emoji}  [b]{habit.name}[/]    {badge}")

        self.query_one("#heatmap", HeatmapWidget).update_view(habit, stats, self._range, self._week_start)

        # Analytics
        self.query_one("#trend-chart", TrendChartWidget).update_view(stats)
        self.query_one("#dow-chart", DayOfWeekWidget).update_view(stats)

        # Metric tiles
        self.query_one("#m-today", MetricTile).set_metric(
            "📅", today_value(stats), "TODAY", today_color(stats)
        )
        self.query_one("#m-streak", MetricTile).set_metric(
            "🔥", f"{stats.current_streak}", "CURRENT STREAK", C_ACCENT
        )
        self.query_one("#m-best", MetricTile).set_metric(
            "🏆", f"{stats.longest_streak}", "LONGEST STREAK", "#22d3ee"
        )
        self.query_one("#m-rate", MetricTile).set_metric(
            "📊", f"{stats.completion_rate * 100:.0f}%", "COMPLETION", C_SUCCESS
        )

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if isinstance(event.item, HabitListItem):
            self._focused_day = None
            self._update_detail(event.item.habit)

    def _selected_habit(self) -> Habit | None:
        item = self.query_one("#habit-list", ListView).highlighted_child
        return item.habit if isinstance(item, HabitListItem) else None

    def select_habit_by_name(self, name: str) -> None:
        lv = self.query_one("#habit-list", ListView)
        for idx, item in enumerate(lv.query(HabitListItem)):
            if item.habit.name == name:
                lv.index = idx
                self._update_detail(item.habit)
                break
        lv.focus()

    def done_habit_by_name(self, name: str) -> None:
        self.select_habit_by_name(name)
        self.action_mark_done()

    def _reload_habit(self, h: Habit) -> None:
        since, _ = range_dates(self._range)
        self._stats[h.id] = build_stats(h, get_entries(h.id), today=date.today(), since=since)
        for item in self.query_one("#habit-list", ListView).query(HabitListItem):
            if item.habit.id == h.id:
                item.refresh_stats(self._stats[h.id])
                break
        self._update_detail(h)
        # Backfill edits keep the selected day's detail open with refreshed values.
        if self._focused_day is not None:
            self._show_day_detail(h, self._focused_day)

    def _target_day(self) -> date:
        """The day logging actions apply to: a selected heatmap cell, else today."""
        return self._focused_day or date.today()

    def _show_day_detail(self, habit: Habit, day: date) -> None:
        from habit_tracker.storage import get_entry
        entry = get_entry(habit.id, day)
        detail = self.query_one("#day-detail", DayDetailWidget)
        detail.border_title = f"  {day.strftime('%a, %d %b %Y')}  "
        detail.add_class("-visible")
        detail.show_day(day, entry, habit)

    def on_heatmap_widget_day_selected(self, event: HeatmapWidget.DaySelected) -> None:
        h = self._selected_habit()
        if h is None:
            return
        self._focused_day = event.day
        self._show_day_detail(h, event.day)

    # ── Responsive layout ─────────────────────────────────────────────────────
    def on_resize(self, event) -> None:  # type: ignore[override]
        compact = event.size.width < 100
        if compact == self._compact:
            return
        self._compact = compact
        self.query_one("#sidebar").styles.width = 8 if compact else 34
        self.query_one("#analytics-row").display = not compact
        for item in self.query(HabitListItem):
            item.set_compact(compact)

    # ── Actions ───────────────────────────────────────────────────────────────
    def _day_label(self, day: date) -> str:
        return "today" if day == date.today() else day.isoformat()

    def action_mark_done(self) -> None:
        h = self._selected_habit()
        if h is None:
            return
        day = self._target_day()
        log_entry(h.id, day)
        self._reload_habit(h)
        self.notify(f"✓ {h.name} logged for {self._day_label(day)}", title="Done")

    def action_mark_undo(self) -> None:
        h = self._selected_habit()
        if h is None:
            return
        day = self._target_day()
        if remove_entry(h.id, day):
            self._reload_habit(h)
            self.notify(f"↩ Removed {self._day_label(day)}'s entry for {h.name}", title="Undo")
        else:
            self.notify(f"No entry for {self._day_label(day)} ({h.name})", severity="warning")

    def action_add_habit(self) -> None:
        inp = self.query_one("#add-input", Input)
        inp.add_class("-active")
        inp.focus()

    def action_log_count(self) -> None:
        if self._selected_habit() is None:
            return
        inp = self.query_one("#count-input", Input)
        inp.add_class("-active")
        inp.focus()

    def action_add_note(self) -> None:
        h = self._selected_habit()
        if h is None:
            return
        inp = self.query_one("#note-input", Input)
        from habit_tracker.storage import get_entry
        existing = get_entry(h.id, self._target_day())
        inp.value = existing.notes or "" if existing else ""
        inp.add_class("-active")
        inp.focus()

    def action_search(self) -> None:
        inp = self.query_one("#search-input", Input)
        inp.add_class("-active")
        inp.focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id != "search-input":
            return
        query = event.value.strip().lower()
        if query.startswith("cat:"):
            cat = query[4:].strip()
            self._filtered_habits = [
                h for h in self._habits if h.category and cat in h.category.lower()
            ]
        elif query:
            self._filtered_habits = [
                h for h in self._habits
                if query in h.name.lower()
                or (h.category and query in h.category.lower())
            ]
        else:
            self._filtered_habits = self._habits
        self._rebuild_list(self._filtered_habits)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        # Only the four bottom overlay inputs are handled here; Inputs inside modal
        # screens emit their own Submitted and must not be treated as "add habit".
        if event.input.id == "count-input":
            self._handle_count_submitted(event.value.strip())
        elif event.input.id == "note-input":
            self._handle_note_submitted(event.value.strip())
        elif event.input.id == "search-input":
            # Enter on search keeps filter active and focuses the list
            self.query_one("#habit-list", ListView).focus()
        elif event.input.id == "add-input":
            self._handle_add_submitted(event.value.strip())

    def _handle_add_submitted(self, name: str) -> None:
        inp = self.query_one("#add-input", Input)
        inp.remove_class("-active")
        inp.value = ""
        if name:
            from habit_tracker.storage import get_habit
            if get_habit(name) is None:
                create_habit(name)
                self.notify(f"Created habit: {name}", title="Added")
            else:
                self.notify(f"Habit '{name}' already exists", severity="warning")
            self._load_habits()
        self.query_one("#habit-list", ListView).focus()

    def _handle_note_submitted(self, text: str) -> None:
        inp = self.query_one("#note-input", Input)
        inp.remove_class("-active")
        inp.value = ""
        h = self._selected_habit()
        if h and text:
            day = self._target_day()
            set_entry_note(h.id, day, text)
            self._reload_habit(h)
            self.notify(f"📝 Note saved for {h.name} ({self._day_label(day)})", title="Note")
        self.query_one("#habit-list", ListView).focus()

    def _handle_count_submitted(self, raw: str) -> None:
        inp = self.query_one("#count-input", Input)
        inp.remove_class("-active")
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
            day = self._target_day()
            log_entry(h.id, day, count=n)
            self._reload_habit(h)
            self.notify(f"✓ {h.name} logged ×{n} for {self._day_label(day)}", title="Logged")
        self.query_one("#habit-list", ListView).focus()

    def action_cancel_input(self) -> None:
        cleared_search = False
        had_active_input = False
        for inp_id in ("#add-input", "#count-input", "#note-input", "#search-input"):
            inp = self.query_one(inp_id, Input)
            if "-active" in inp.classes:
                had_active_input = True
                if inp_id == "#search-input":
                    cleared_search = True
                inp.remove_class("-active")
                inp.value = ""
        if cleared_search:
            self._filtered_habits = self._habits
            self._rebuild_list(self._habits)
        # No input was open → Esc dismisses the day-detail overlay / backfill focus.
        if not had_active_input and self._focused_day is not None:
            self._focused_day = None
            self.query_one("#day-detail", DayDetailWidget).clear()
            h = self._selected_habit()
            if h is not None:
                self._update_detail(h)
        self.query_one("#habit-list", ListView).focus()

    def action_edit_habit(self) -> None:
        h = self._selected_habit()
        if h is None:
            return

        def _on_save(values: dict | None) -> None:
            if not values:
                return
            from habit_tracker.storage import get_habit, update_habit, _UNSET
            import sqlite3
            if values["name"] != h.name and get_habit(values["name"]):
                self.notify(f"Habit '{values['name']}' already exists", severity="warning")
                return
            try:
                update_habit(
                    h.id,
                    name=values["name"],
                    emoji=values["emoji"],
                    color=values["color"],
                    target=values["target"],
                    schedule=values["schedule"],
                    category=values["category"],
                )
            except sqlite3.IntegrityError:
                self.notify(f"Habit '{values['name']}' already exists", severity="warning")
                return
            self.notify(f"Updated: {values['name']}", title="Edited")
            self._load_habits()
            self.select_habit_by_name(values["name"])

        self.push_screen(EditHabitScreen(h), _on_save)

    def action_open_settings(self) -> None:
        def _on_save(values: dict | None) -> None:
            if not values:
                return
            from habit_tracker.config import save_config, load_config
            save_config({**load_config(), **values})
            self._week_start = values["week_start"]
            self._set_range(values["default_range"])
            self.notify("Settings saved", title="Settings")

        self.push_screen(SettingsScreen(self._week_start, self._range), _on_save)

    def action_delete_habit(self) -> None:
        h = self._selected_habit()
        if h is None:
            return
        label = f"{h.emoji} {h.name}" if h.emoji else h.name

        def _on_confirm(confirmed: bool | None) -> None:
            if not confirmed:
                return
            delete_habit(h.name)
            self.notify(f"Deleted: {h.name}", severity="warning", title="Removed")
            self._load_habits()

        self.push_screen(
            ConfirmScreen(f"Delete '{label}' and all its entries?"),
            _on_confirm,
        )

    def action_set_range_year(self) -> None:
        self._set_range("year")

    def action_set_range_quarter(self) -> None:
        self._set_range("quarter")

    def action_set_range_month(self) -> None:
        self._set_range("month")

    def _set_range(self, r: str) -> None:
        self._range = r
        self._focused_day = None  # a selected cell may fall outside the new range
        self.query_one("#range-pills", Static).update(self._range_pills())
        h = self._selected_habit()
        if h:
            self._reload_habit(h)

    def action_cursor_down(self) -> None:
        self.query_one("#habit-list", ListView).action_cursor_down()

    def action_cursor_up(self) -> None:
        self.query_one("#habit-list", ListView).action_cursor_up()
