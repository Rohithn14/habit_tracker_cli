# habit-tracker

Terminal habit tracker with GitHub-style contribution heatmaps, streaks, intensity shading, and an interactive TUI — all in your terminal.

## Features

- **GitHub-accurate heatmap** — 7-row × week-column grid, month labels, 5-shade green intensity palette
- **Intensity levels** — if you set a daily target (`--target 3`), deeper green = more done that day
- **Stats** — current streak, longest streak, completion %, total completions
- **Multiple time ranges** — year, quarter, month (CLI `--range` flag or TUI keypress)
- **Fast CLI** — `habit add / done / undo / list / show / summary / rm / export / import`
- **Interactive TUI** — `habit tui` — sidebar list, heatmap detail, keybindings
- **Shell startup summary** — compact per-habit sparkline + streak + today status, shown on every terminal open

## Install

```bash
uv tool install .
```

This puts `habit` on your PATH.

## Quick start

```bash
habit add "Morning Run" --emoji 🏃 --target 3
habit add "Read 30min" --emoji 📚 --target 1
habit add "Meditate"   --emoji 🧘

habit done "Morning Run" --count 2
habit done "Read 30min"
habit done "Morning Run" --date 2026-06-04 --count 3   # back-date

habit list
habit show "Morning Run" --range quarter
habit summary

habit tui
```

## CLI reference

| Command | Description |
|---------|-------------|
| `habit add NAME [--emoji E] [--target N] [--color C]` | Create a habit |
| `habit done NAME [--date YYYY-MM-DD] [--count N]` | Log a day done |
| `habit undo NAME [--date YYYY-MM-DD]` | Remove a logged entry |
| `habit list [--all]` | List habits with streak + today status |
| `habit show NAME [--range year\|quarter\|month]` | Full heatmap + stats |
| `habit summary [--range ...]` | Compact startup summary |
| `habit rm NAME [--archive] [--force]` | Delete or archive |
| `habit export [-o FILE]` | Export to JSON |
| `habit import FILE [--overwrite]` | Import from JSON |
| `habit tui` | Interactive TUI |
| `habit shell-install [--remove]` | Add/remove ~/.zshrc hook |

## TUI keybindings

| Key | Action |
|-----|--------|
| `d` | Mark today done |
| `u` | Undo today |
| `a` | Add new habit |
| `x` | Delete selected habit |
| `1` / `2` / `3` | Switch to year / quarter / month range |
| `j` / `↓` | Move down |
| `k` / `↑` | Move up |
| `q` | Quit |

## Shell startup hook

After confirming the app works, wire it into your shell:

```bash
habit shell-install
```

This appends an idempotent block to `~/.zshrc` that runs `habit summary` on every interactive terminal open. Remove it with:

```bash
habit shell-install --remove
```

## Data storage

- **Database**: `~/.local/share/habit-tracker/habits.db` (SQLite, WAL mode)
- **Config**: `~/.config/habit-tracker/config.toml` (optional, TOML)
- **Backup**: `habit export -o backup.json` / `habit import backup.json`

## Development

```bash
uv run habit ...       # run from source
uv run pytest          # run tests
```
