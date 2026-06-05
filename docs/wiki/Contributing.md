# Contributing

## Dev setup

```bash
git clone https://github.com/Rohithn14/habit_tracker_cli.git
cd habit_tracker_cli
uv sync --group dev
uv run pytest          # should be 41 tests, all passing
uv run habit --help
```

## Project layout

```
src/habit_tracker/
  cli.py         — Typer commands (add/done/undo/list/show/summary/rm/export/import/tui/shell-install)
  storage.py     — SQLite CRUD, WAL mode, upsert via ON CONFLICT
  stats.py       — streak, completion rate, intensity bucketing
  models.py      — Habit, Entry, HabitStats dataclasses
  config.py      — platformdirs paths + config.toml loading
  shell.py       — ~/.zshrc hook install/remove/check
  render/
    heatmap.py       — Rich GitHub-style grid
    stats_panel.py   — Rich stats panel
    summary.py       — compact sparkline per habit
  tui/
    app.py       — Textual App (lazy-imported to keep shell startup fast)
    widgets.py   — HeatmapWidget, StatsWidget, HabitListItem

tests/
  test_stats.py    — 25 unit tests (intensity, streaks, completion, range_dates)
  test_storage.py  — 16 integration tests (isolated SQLite via monkeypatch)
```

## Writing tests

- New stats logic → `tests/test_stats.py`.
- New storage behavior → `tests/test_storage.py` using the `isolated_db` fixture (redirects `DB_PATH` to `tmp_path`).
- Use `date(2026, 6, 5)` as the fixed `TODAY` constant — keeps tests deterministic.

## Key invariants

1. **`habit summary` must never raise.** It wraps all logic in `try/except: pass`. Any new code path reachable from `summary` must also be silent-safe.

2. **Textual is lazy-imported.** Only inside the `tui` command: `from habit_tracker.tui.app import HabitApp`. Never at module top-level. This keeps cold-start fast.

3. **No method named `_render` on Textual widgets.** Textual calls `_render()` internally with no arguments; naming a method `_render(self, data)` causes a `TypeError`. Use `_build_content` instead (already established in `widgets.py`).

4. **`log_entry` is an upsert.** Calling it twice on the same `(habit_id, date)` overwrites the count — don't add guard logic that assumes idempotency elsewhere.

## Submitting changes

1. Fork and create a branch from `main`.
2. Add or update tests.
3. `uv run pytest` — all tests must pass.
4. Open a PR against `main` with a description of what and why.

Feature branches in this repo use the prefix `feature/` — e.g. `feature/weekly-goals`.
