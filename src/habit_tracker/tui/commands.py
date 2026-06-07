"""Custom command-palette provider for the habit tracker TUI."""
from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from textual.command import DiscoveryHit, Hit, Hits, Provider

if TYPE_CHECKING:
    from habit_tracker.tui.app import HabitApp


class HabitCommands(Provider):
    """Exposes habit actions and per-habit jumps in the Ctrl+P palette."""

    def _commands(self) -> list[tuple[str, str, Callable[[], None]]]:
        app: HabitApp = self.app  # type: ignore[assignment]
        cmds: list[tuple[str, str, Callable[[], None]]] = [
            ("✓  Mark current habit done", "Log today for the selected habit", app.action_mark_done),
            ("#  Log count for today…", "Enter a custom count for the selected habit", app.action_log_count),
            ("↩  Undo today", "Remove today's entry for the selected habit", app.action_mark_undo),
            ("📝  Note for today…", "Attach a text note to today's entry", app.action_add_note),
            ("🔍  Search habits…", "Filter the sidebar by habit name", app.action_search),
            ("+  Add habit…", "Create a new habit", app.action_add_habit),
            ("✎  Edit current habit…", "Edit the selected habit's fields", app.action_edit_habit),
            ("🗑  Delete current habit", "Delete the selected habit and its history", app.action_delete_habit),
            ("⚙  Settings…", "Edit week start and default range", app.action_open_settings),
            ("📅  Range: Year", "Show the whole year", lambda: app._set_range("year")),
            ("📅  Range: Quarter", "Show the current quarter", lambda: app._set_range("quarter")),
            ("📅  Range: Month", "Show the current month", lambda: app._set_range("month")),
        ]

        # Per-habit jump + quick-log commands
        for habit in app._habits:
            emoji = habit.emoji or "●"
            name = habit.name
            cmds.append((
                f"{emoji}  Open: {name}",
                "Jump to this habit",
                lambda n=name: app.select_habit_by_name(n),
            ))
            cmds.append((
                f"{emoji}  Done today: {name}",
                "Mark this habit done for today",
                lambda n=name: app.done_habit_by_name(n),
            ))
        return cmds

    async def discover(self) -> Hits:
        """Commands shown when the palette opens with no query."""
        for display, help_text, callback in self._commands():
            yield DiscoveryHit(display, callback, help=help_text)

    async def search(self, query: str) -> Hits:
        """Fuzzy-match commands against the user's query."""
        matcher = self.matcher(query)
        for display, help_text, callback in self._commands():
            score = matcher.match(display)
            if score > 0:
                yield Hit(score, matcher.highlight(display), callback, help=help_text)
