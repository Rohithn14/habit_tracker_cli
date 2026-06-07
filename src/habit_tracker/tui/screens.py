"""Modal screens for the TUI (confirmation dialogs, forms)."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Select

from habit_tracker.colors import colors_hint, is_valid_color
from habit_tracker.models import Habit
from habit_tracker.schedule import is_valid_schedule


class ConfirmScreen(ModalScreen[bool]):
    """A yes/no confirmation dialog. Dismisses with True (confirm) or False (cancel)."""

    CSS = """
    ConfirmScreen {
        align: center middle;
    }
    ConfirmScreen #dialog {
        width: 52;
        height: auto;
        padding: 1 2;
        border: round $accent;
        background: $surface;
    }
    ConfirmScreen #prompt {
        width: 100%;
        margin-bottom: 1;
    }
    ConfirmScreen #buttons {
        height: auto;
        align-horizontal: right;
    }
    ConfirmScreen Button {
        margin-left: 2;
    }
    """

    BINDINGS = [
        Binding("y", "confirm", "Yes", show=False),
        Binding("n,escape", "cancel", "No", show=False),
    ]

    def __init__(self, prompt: str, confirm_label: str = "Delete") -> None:
        super().__init__()
        self._prompt = prompt
        self._confirm_label = confirm_label

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(self._prompt, id="prompt")
            with Horizontal(id="buttons"):
                yield Button("Cancel", variant="default", id="cancel")
                yield Button(self._confirm_label, variant="error", id="confirm")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "confirm")

    def action_confirm(self) -> None:
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)


_FORM_CSS = """
    %(name)s {
        align: center middle;
    }
    %(name)s #dialog {
        width: 60;
        height: auto;
        padding: 1 2;
        border: round $accent;
        background: $surface;
    }
    %(name)s Label {
        margin-top: 1;
        color: $text-muted;
    }
    %(name)s #title {
        margin-top: 0;
        text-style: bold;
        color: $accent;
    }
    %(name)s #buttons {
        height: auto;
        margin-top: 1;
        align-horizontal: right;
    }
    %(name)s Button {
        margin-left: 2;
    }
"""


class EditHabitScreen(ModalScreen[dict | None]):
    """Form to edit a habit's fields. Dismisses with a dict of new values, or None."""

    CSS = _FORM_CSS % {"name": "EditHabitScreen"}

    BINDINGS = [Binding("escape", "cancel", "Cancel", show=False)]

    def __init__(self, habit: Habit) -> None:
        super().__init__()
        self._habit = habit

    def compose(self) -> ComposeResult:
        h = self._habit
        with Vertical(id="dialog"):
            yield Label(f"Edit {h.name}", id="title")
            yield Label("Name")
            yield Input(value=h.name, id="f-name")
            yield Label("Emoji")
            yield Input(value=h.emoji, id="f-emoji")
            yield Label(f"Color ({colors_hint()})")
            yield Input(value=h.color, id="f-color")
            yield Label("Target (blank = none)")
            yield Input(value=str(h.target) if h.target else "", id="f-target")
            yield Label("Schedule (daily | weekly:N | dow:1,3,5)")
            yield Input(value=h.schedule or "daily", id="f-schedule")
            yield Label("Category")
            yield Input(value=h.category or "", id="f-category")
            with Horizontal(id="buttons"):
                yield Button("Cancel", variant="default", id="cancel")
                yield Button("Save", variant="success", id="save")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.dismiss(None)
            return
        self._submit()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        # Enter in any field submits the form; stop it bubbling to the app.
        event.stop()
        self._submit()

    def _value(self, sel: str) -> str:
        return self.query_one(sel, Input).value.strip()

    def _submit(self) -> None:
        name = self._value("#f-name")
        if not name:
            self.app.notify("Name cannot be empty", severity="warning")
            return
        color = self._value("#f-color") or "green"
        if not is_valid_color(color):
            self.app.notify(f"Unknown color. Choose: {colors_hint()}", severity="warning")
            return
        schedule = self._value("#f-schedule") or "daily"
        if not is_valid_schedule(schedule):
            self.app.notify("Invalid schedule. Use daily | weekly:N | dow:1,3,5", severity="warning")
            return
        target_raw = self._value("#f-target")
        target: int | None = None
        if target_raw:
            try:
                target = int(target_raw)
            except ValueError:
                self.app.notify("Target must be a whole number", severity="warning")
                return
        self.dismiss({
            "name": name,
            "emoji": self._value("#f-emoji"),
            "color": color,
            "target": target,
            "schedule": None if schedule.lower() == "daily" else schedule,
            "category": self._value("#f-category") or None,
        })

    def action_cancel(self) -> None:
        self.dismiss(None)


class SettingsScreen(ModalScreen[dict | None]):
    """Edit week_start and default_range. Dismisses with a config dict, or None."""

    CSS = _FORM_CSS % {"name": "SettingsScreen"}

    BINDINGS = [Binding("escape", "cancel", "Cancel", show=False)]

    def __init__(self, week_start: str, default_range: str) -> None:
        super().__init__()
        self._week_start = week_start
        self._default_range = default_range

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Settings", id="title")
            yield Label("Week starts on")
            yield Select(
                [("Sunday", "sunday"), ("Monday", "monday")],
                value=self._week_start, allow_blank=False, id="s-week-start",
            )
            yield Label("Default range")
            yield Select(
                [("Year", "year"), ("Quarter", "quarter"), ("Month", "month")],
                value=self._default_range, allow_blank=False, id="s-range",
            )
            with Horizontal(id="buttons"):
                yield Button("Cancel", variant="default", id="cancel")
                yield Button("Save", variant="success", id="save")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.dismiss(None)
            return
        self.dismiss({
            "week_start": self.query_one("#s-week-start", Select).value,
            "default_range": self.query_one("#s-range", Select).value,
        })

    def action_cancel(self) -> None:
        self.dismiss(None)
