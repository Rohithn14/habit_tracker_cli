"""Pilot-driven interaction tests for the Textual TUI."""
from datetime import date, timedelta

import pytest


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    db_path = tmp_path / "habits.db"
    monkeypatch.setattr("habit_tracker.storage.DB_PATH", db_path)
    monkeypatch.setattr("habit_tracker.config.DATA_DIR", tmp_path)
    monkeypatch.setattr("habit_tracker.config.CONFIG_DIR", tmp_path)
    monkeypatch.setattr("habit_tracker.config.CONFIG_PATH", tmp_path / "config.toml")
    from habit_tracker.storage import init_db
    init_db()
    yield db_path


def _make_habit(name="run", **kw):
    from habit_tracker.storage import create_habit
    return create_habit(name, **kw)


@pytest.mark.asyncio
async def test_mark_done_logs_today():
    from habit_tracker.tui.app import HabitApp
    from habit_tracker.storage import get_entry
    h = _make_habit()
    app = HabitApp()
    async with app.run_test() as pilot:
        await pilot.press("d")
        await pilot.pause()
    assert get_entry(h.id, date.today()) is not None


@pytest.mark.asyncio
async def test_delete_requires_confirmation():
    from habit_tracker.tui.app import HabitApp
    from habit_tracker.tui.screens import ConfirmScreen
    from habit_tracker.storage import get_habit
    _make_habit("drop-me")
    app = HabitApp()
    async with app.run_test() as pilot:
        await pilot.press("x")
        await pilot.pause()
        # A confirmation screen must be on the stack; habit still present.
        assert isinstance(app.screen, ConfirmScreen)
        assert get_habit("drop-me") is not None
        await pilot.press("n")  # cancel
        await pilot.pause()
        assert get_habit("drop-me") is not None


@pytest.mark.asyncio
async def test_delete_confirmed_removes_habit():
    from habit_tracker.tui.app import HabitApp
    from habit_tracker.storage import get_habit
    _make_habit("drop-me")
    app = HabitApp()
    async with app.run_test() as pilot:
        await pilot.press("x")
        await pilot.pause()
        await pilot.press("y")  # confirm
        await pilot.pause()
        assert get_habit("drop-me") is None


@pytest.mark.asyncio
async def test_backfill_logs_selected_day():
    from habit_tracker.tui.app import HabitApp
    from habit_tracker.tui.widgets import HeatmapWidget
    from habit_tracker.storage import get_entry
    h = _make_habit()
    past = date.today() - timedelta(days=10)
    app = HabitApp()
    async with app.run_test() as pilot:
        # Simulate selecting a past heatmap cell.
        app.post_message(HeatmapWidget.DaySelected(past))
        await pilot.pause()
        assert app._focused_day == past
        await pilot.press("d")
        await pilot.pause()
    assert get_entry(h.id, past) is not None
    assert get_entry(h.id, date.today()) is None  # today untouched


@pytest.mark.asyncio
async def test_edit_modal_updates_habit():
    from habit_tracker.tui.app import HabitApp
    from habit_tracker.tui.screens import EditHabitScreen
    from habit_tracker.storage import get_habit
    _make_habit("run", emoji="🏃")
    app = HabitApp()
    async with app.run_test() as pilot:
        await pilot.press("e")
        await pilot.pause()
        assert isinstance(app.screen, EditHabitScreen)
        name_input = app.screen.query_one("#f-name")
        # The form fields must actually be visible (regression: the app's global
        # Input rule once hid every Input, including those inside modals).
        assert name_input.display is True
        assert app.screen.query_one("#f-category").display is True
        name_input.value = "jog"
        sched_input = app.screen.query_one("#f-schedule")
        sched_input.value = "weekly:3"
        app.screen.query_one("#save").press()
        await pilot.pause()
    h = get_habit("jog")
    assert h is not None
    assert h.schedule == "weekly:3"
    assert get_habit("run") is None


@pytest.mark.asyncio
async def test_edit_modal_enter_submits_not_creates_habit():
    # Regression: Enter inside the modal once bubbled to the app's add-habit handler,
    # turning the typed category into a brand-new habit.
    from habit_tracker.tui.app import HabitApp
    from habit_tracker.storage import get_habit, list_habits
    _make_habit("run")
    app = HabitApp()
    async with app.run_test() as pilot:
        await pilot.press("e")
        await pilot.pause()
        cat = app.screen.query_one("#f-category")
        cat.focus()
        cat.value = "fitness"
        await pilot.press("enter")
        await pilot.pause()
    # Exactly one habit, with the category applied — no phantom "fitness" habit.
    names = [h.name for h in list_habits()]
    assert names == ["run"]
    assert get_habit("run").category == "fitness"
    assert get_habit("fitness") is None


@pytest.mark.asyncio
async def test_settings_persist():
    from habit_tracker.tui.app import HabitApp
    from habit_tracker.tui.screens import SettingsScreen
    from habit_tracker.config import load_config
    _make_habit()
    app = HabitApp()
    async with app.run_test() as pilot:
        await pilot.press("comma")
        await pilot.pause()
        assert isinstance(app.screen, SettingsScreen)
        app.screen.query_one("#s-week-start").value = "monday"
        app.screen.query_one("#s-range").value = "month"
        app.screen.query_one("#save").press()
        await pilot.pause()
    cfg = load_config()
    assert cfg["week_start"] == "monday"
    assert cfg["default_range"] == "month"


@pytest.mark.asyncio
async def test_category_filter():
    from habit_tracker.tui.app import HabitApp
    from habit_tracker.tui.widgets import HabitListItem
    _make_habit("gym", category="fitness")
    _make_habit("read", category="learning")
    app = HabitApp()
    async with app.run_test() as pilot:
        await pilot.press("slash")
        await pilot.pause()
        search = app.query_one("#search-input")
        search.value = "cat:fitness"
        await pilot.pause()
        names = [i.habit.name for i in app.query(HabitListItem)]
    assert names == ["gym"]
