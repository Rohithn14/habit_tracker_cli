# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
uv run pytest                          # run all 41 tests
uv run pytest tests/test_stats.py      # run a single test file
uv run pytest -k "test_current_streak" # run a single test by name
uv run habit --help                    # run CLI from source
uv run habit tui                       # launch TUI
uv tool install .                      # install `habit` onto PATH
```

## Architecture

The data flow is: **CLI/TUI** → **storage.py** (SQLite) + **stats.py** (pure logic) → **render/** (Rich output) or **tui/** (Textual widgets).

**`models.py`** — three dataclasses used everywhere: `Habit`, `Entry`, `HabitStats`. No methods.

**`storage.py`** — all SQLite access via `_conn()` context manager (WAL, foreign keys ON). `log_entry` is an upsert (`ON CONFLICT DO UPDATE`). Tests redirect `DB_PATH` via `monkeypatch` — never import `DB_PATH` at call-site, always reference it as `habit_tracker.storage.DB_PATH` so monkeypatching works.

**`stats.py`** — pure functions, no I/O. `build_stats(habit, entries, today, since)` assembles `HabitStats`. `intensity_bucket(count, target)` → 0–4 (0=empty, 2=done with no target, 1–4 keyed to fraction of target). `range_dates(range_name, today)` → `(since, until)`.

**`render/heatmap.py`** — GitHub-accurate grid: aligns grid start to Sunday via `(weekday+1)%7` offset, renders month labels then 7 day rows (day labels only on rows 1/3/5 = Mon/Wed/Fri). Palette: `["#161b22","#0e4429","#006d32","#26a641","#39d353"]`.

**`render/summary.py`** — compact startup view: one `Text` line per habit (emoji, name, 28-char sparkline over last 4 weeks, streak, today mark, completion%). Must never raise — called from `habit summary` which wraps everything in `try/except: pass`.

**`tui/app.py`** + **`tui/widgets.py`** — Textual app. Lazy-imported: only inside the `tui` CLI command, never at module top level (keeps shell startup fast). A custom `HABIT_THEME` (`textual.theme.Theme`) is registered in `on_mount` and drives `$primary`/`$secondary`/`$accent` in the CSS; markup strings use the matching hardcoded hex constants (`C_PRIMARY`, `C_ACCENT`, …) since Rich `Text.from_markup` does not resolve `$` theme tokens. Widgets: `HabitListItem` (two-line sidebar card), `HeatmapWidget` (`update_view(habit, stats, range)`), `MetricTile` (`set_metric(icon, value, label, color)` — four instances form the stats row). Widget methods that rebuild display are named `_build_content` — never `_render` (conflicts with Textual's internal rendering pipeline and causes `TypeError`). The habit list must be explicitly `.focus()`-ed in `on_mount`, otherwise a hidden `Input` can capture keystrokes meant for app bindings.

**`shell.py`** — idempotent `~/.zshrc` block management. Uses `_MARKER_START`/`_MARKER_END` string delimiters to locate and strip the block.

**`cli.py`** — Typer app. `_callback` calls `init_db()` on every invocation. `summary` command wraps all logic in `try/except: pass`. `tui` command does `from habit_tracker.tui.app import HabitApp` inline.

## Key invariants

- **`habit summary` must never raise.** Any code path reachable from the `summary` command must be silent-safe.
- **Textual is always a lazy import.** Never import from `habit_tracker.tui` at module level.
- **`log_entry` is an upsert** — calling it twice on the same `(habit_id, date)` overwrites the count; no guards needed at call sites.
- **No Textual widget method named `_render`.** Use `_build_content` (already established convention in `widgets.py`).

## Tests

`tests/test_storage.py` uses an `isolated_db` fixture (`autouse=True`) that monkeypatches `habit_tracker.storage.DB_PATH` and `habit_tracker.config.DATA_DIR` to `tmp_path`, then calls `init_db()`. Fixed date constant `TODAY = date(2026, 6, 5)` is used in both test files for determinism.
