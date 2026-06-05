# Contributing

## Dev setup

```bash
git clone https://github.com/Rohithn14/habit_tracker_cli.git
cd habit_tracker_cli
uv sync --group dev
```

Run the CLI from source:

```bash
uv run habit --help
```

Run tests:

```bash
uv run pytest
```

## Project layout

```
src/habit_tracker/
  cli.py         # Typer commands
  storage.py     # SQLite CRUD
  stats.py       # streak / completion / intensity logic
  models.py      # Habit, Entry, HabitStats dataclasses
  config.py      # platformdirs paths + config.toml loading
  shell.py       # ~/.zshrc hook install/remove
  render/
    heatmap.py   # GitHub-style Rich grid
    stats_panel.py
    summary.py   # compact startup sparkline
  tui/
    app.py       # Textual App
    widgets.py   # HeatmapWidget, StatsWidget, HabitListItem
tests/
  test_stats.py    # 25 unit tests
  test_storage.py  # 16 integration tests (isolated SQLite)
```

## Guidelines

- New logic in `stats.py` needs unit tests in `tests/test_stats.py`.
- Storage changes need tests in `tests/test_storage.py` using the `isolated_db` fixture.
- `habit summary` must never raise — wrap any new startup path in `try/except`.
- Textual widget methods must not be named `_render` (conflicts with Textual internals); use `_build_content` instead.
- Keep Textual as a lazy import (`from habit_tracker.tui.app import HabitApp` inside the `tui` command) so shell startup stays fast.

## Submitting a PR

1. Fork the repo and create a branch from `main`.
2. Make your changes with tests.
3. Run `uv run pytest` — all tests must pass.
4. Open a PR against `main` with a clear description of what changes and why.
