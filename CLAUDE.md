# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
uv run pytest                          # run all 131 tests
uv run pytest tests/test_stats.py      # run a single test file
uv run pytest -k "test_current_streak" # run a single test by name
uv run pytest tests/test_tui.py        # Pilot-driven TUI interaction tests
uv run habit --help                    # run CLI from source
uv run habit tui                       # launch TUI
uv tool install .                      # install `habit` onto PATH
```

## Architecture

The data flow is: **CLI/TUI** → **storage.py** (SQLite) + **stats.py** (pure logic) → **render/** (Rich output) or **tui/** (Textual widgets).

**`models.py`** — three dataclasses used everywhere: `Habit`, `Entry`, `HabitStats`. `Habit` has fields `schedule` (str | None) and `category` (str | None), plus a `label` property (`"{emoji} {name}"`, name only when no emoji) — use `h.label` instead of re-deriving the string at call sites.

**`storage.py`** — all SQLite access via `_conn()` context manager (WAL, foreign keys ON). `log_entry` is an upsert (`ON CONFLICT DO UPDATE`); `update_habit(id, *, ...)` builds a dynamic `UPDATE` and uses an `_UNSET` sentinel so `None` clears a column vs. leaving it. **Schema evolution is versioned** via `PRAGMA user_version` and the ordered `_MIGRATIONS` list — index *i* migrates version *i*→*i+1*; `init_db()` applies pending migrations in one transaction. Append-only: never edit/reorder an existing migration. All habit SELECTs share the `_HABIT_COLS` constant (keep it in sync with `_row_to_habit`). Tests redirect `DB_PATH` via `monkeypatch` — never import `DB_PATH` at call-site, always reference it as `habit_tracker.storage.DB_PATH`.

**`stats.py`** — pure functions, no I/O. `build_stats(habit, entries, today, since)` assembles `HabitStats`, routing streaks/completion through the schedule-aware functions in `schedule.py`. `intensity_bucket(count, target)` → 0–4. `range_dates(range_name, today)` → `(since, until)`; accepts named ranges plus `last:Nd`/`last:Nw` and explicit `YYYY-MM-DD:YYYY-MM-DD`.

**`schedule.py`** — habit frequency encoded as a string on `Habit.schedule`: `daily`/None, `weekly:N` (N times per ISO week), or `dow:1,3,5` (ISO weekdays, 1=Mon). `parse_schedule`, `is_due`, and `scheduled_{current,longest}_streak`/`scheduled_completion_rate` implement schedule-aware stats (dow streaks skip non-due days; weekly streaks count met weeks). Daily behavior is identical to the pre-schedule logic.

**`config.py`** — `load_config` routes through `validate_config` (clamps `default_range`/`week_start`, drops unknown keys). `save_config(cfg)` validates then writes TOML via `tomli-w` (stdlib `tomllib` is read-only).

**`render/heatmap.py`** — GitHub-accurate grid: aligns grid start to Sunday via `(weekday+1)%7` offset, renders month labels then 7 day rows (day labels only on rows 1/3/5 = Mon/Wed/Fri). NB: the CLI renderer's palette (`["#161b22","#0e4429","#006d32","#26a641","#39d353"]`) differs from the TUI heatmap's `_PALETTE` in `tui/widgets.py` (`["#30363d","#ef4444","#f59e0b","#22c55e","#06b6d4"]`) — they are intentionally separate.

**`render/summary.py`** — compact startup view: one `Text` line per habit (emoji, name, 28-char sparkline over last 4 weeks, streak, today mark, completion%). Must never raise — called from `habit summary` which wraps everything in `try/except: pass`.

**`tui/app.py`** + **`tui/widgets.py`** — Textual app. Lazy-imported: only inside the `tui` CLI command, never at module top level (keeps shell startup fast). A custom `HABIT_THEME` (`textual.theme.Theme`) is registered in `on_mount` and drives `$primary`/`$secondary`/`$accent` in the CSS; markup strings use the matching hardcoded hex constants (`C_PRIMARY`, `C_ACCENT`, …) since Rich `Text.from_markup` does not resolve `$` theme tokens. Widgets: `HabitListItem` (two-line sidebar card), `HeatmapWidget` (`update_view(habit, stats, range)`), `MetricTile` (`set_metric(icon, value, label, color)` — four instances form the stats row). Widget methods that rebuild display are named `_build_content` — never `_render` (conflicts with Textual's internal rendering pipeline and causes `TypeError`). The habit list must be explicitly `.focus()`-ed in `on_mount`, otherwise a hidden `Input` can capture keystrokes meant for app bindings. `HabitListItem(habit, stats, compact=...)` takes its compact flag at construction — set_compact after `lv.append(...)` runs before the child `Static` mounts, so the initial label must be correct up front (set_compact guards `NoMatches` for the same reason).

**`tui/screens.py`** — `ModalScreen` subclasses: `ConfirmScreen` (y/n delete guard — deletion is never instant), `EditHabitScreen` (form returning a values dict, `e` key), `SettingsScreen` (week_start/default_range → `save_config`, `,` key). Backfill logging: clicking a heatmap cell sets `HabitApp._focused_day`, and `_target_day()` makes the `d`/`c`/`u`/`n` actions apply to that day instead of today (Esc clears it).

**`tui/commands.py`** — `HabitCommands(Provider)` powers the Ctrl+P command palette (registered via `HabitApp.COMMANDS`). It builds a fresh command list each search from `app._habits`, yielding both static actions (mark done, log count, add, delete, range switches) and per-habit `Open:`/`Done today:` jumps. The palette's dated default look is overridden in `HabitApp.CSS` (selectors: `CommandPalette > Vertical`, `CommandPalette #--input`, `SearchIcon`, `CommandList`, `.option-list--option-highlighted`).

**Today's count**: `HabitStats.today_count` (sum of today's entry counts) drives the title-bar badge, sidebar sub-line, and the first `TODAY` metric tile. `today_value()`/`today_color()` in `widgets.py` format it (green if target met, amber if partial).

**`shell.py`** — idempotent `~/.zshrc` block management. Uses `_MARKER_START`/`_MARKER_END` string delimiters to locate and strip the block.

**`cli.py`** — Typer app. `_callback` calls `init_db()` on every invocation. `summary` command wraps all logic in `try/except: pass`. `tui` command does `from habit_tracker.tui.app import HabitApp` inline.

## Key invariants

- **`habit summary` must never raise.** Any code path reachable from the `summary` command must be silent-safe.
- **Textual is always a lazy import.** Never import from `habit_tracker.tui` at module level.
- **`log_entry` is an upsert** — calling it twice on the same `(habit_id, date)` overwrites the count; no guards needed at call sites.
- **No Textual widget method named `_render`.** Use `_build_content` (already established convention in `widgets.py`).
- **Migrations are append-only.** Add a new callable to `_MIGRATIONS`; never edit or reorder an existing one.
- **Schedule strings round-trip through export/import** and normalize `"daily"` → `NULL`.

## Tests

`tests/test_storage.py` uses an `isolated_db` fixture (`autouse=True`) that monkeypatches `habit_tracker.storage.DB_PATH` and `habit_tracker.config.DATA_DIR` to `tmp_path`, then calls `init_db()`. Fixed date constant `TODAY = date(2026, 6, 5)` is used across test files for determinism. `tests/test_tui.py` drives the TUI with `textual`'s `App.run_test()` Pilot (async; `asyncio_mode = "auto"` is set in `pyproject.toml`, requires `pytest-asyncio`); it also monkeypatches `CONFIG_DIR`/`CONFIG_PATH` so settings writes stay in `tmp_path`.
