# habit-tracker

[![CI](https://github.com/Rohithn14/habit_tracker_cli/actions/workflows/ci.yml/badge.svg)](https://github.com/Rohithn14/habit_tracker_cli/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Terminal habit tracker with GitHub-style contribution heatmaps, streak tracking, intensity shading, and a full interactive TUI — no browser required.

```
🏃 Morning Run  ▁▁▆▆█▆▁▁  🔥 5d  ✓
📚 Read 30min   ▁▃▁▆▃▆█▁  🔥 2d  ·
🧘 Meditate     ▁▁▁▃▆▆▆█  🔥 4d  ✓
```

---

## Features

- **GitHub-accurate heatmap** — 7 weekday rows × week columns, month labels, 5-shade green intensity palette matching GitHub's `#161b22 → #39d353` scale
- **Intensity levels** — set a daily target (`--target 3`); deeper green = more done that day
- **Stats** — current streak, longest streak, completion rate, total completions, today status
- **Multiple time ranges** — year / quarter / month, switchable in real time
- **Fast CLI** (`habit add / done / undo / list / show / summary / rm / export / import`)
- **Interactive TUI** (`habit tui`) — sidebar list, heatmap + stats pane, full keyboard navigation
- **Shell startup summary** — compact per-habit sparkline shown on every terminal open (fast, silent, never breaks the shell)
- **JSON export / import** — full backup and portability

---

## Install

**Recommended — isolated tool install via uv:**

```bash
uv tool install git+https://github.com/Rohithn14/habit_tracker_cli.git
```

This puts `habit` on your `PATH` in an isolated environment.

**From PyPI (once published):**

```bash
pip install habit-tracker
# or
uv tool install habit-tracker
```

**From source:**

```bash
git clone https://github.com/Rohithn14/habit_tracker_cli.git
cd habit_tracker_cli
uv tool install .
```

---

## Quick start

```bash
# Create habits
habit add "Morning Run" --emoji 🏃 --target 3
habit add "Read 30min"  --emoji 📚 --target 1
habit add "Meditate"    --emoji 🧘

# Log today (optionally with a count)
habit done "Morning Run" --count 2
habit done "Read 30min"
habit done "Morning Run" --date 2026-06-01 --count 3   # back-date

# View
habit list
habit show "Morning Run" --range quarter
habit summary

# Interactive TUI
habit tui
```

---

## CLI reference

| Command | Description |
|---------|-------------|
| `habit add NAME [--emoji E] [--target N] [--color C]` | Create a habit |
| `habit done NAME [--date YYYY-MM-DD] [--count N]` | Log a day done |
| `habit undo NAME [--date YYYY-MM-DD]` | Remove a logged entry |
| `habit list [--all]` | List habits (name, streak, today status) |
| `habit show NAME [--range year\|quarter\|month]` | Heatmap + stats panel |
| `habit summary [--range ...]` | Compact sparkline summary |
| `habit rm NAME [--archive] [--force]` | Delete or archive a habit |
| `habit export [-o FILE]` | Export all data to JSON |
| `habit import FILE [--overwrite]` | Import from a JSON export |
| `habit tui` | Launch interactive TUI |
| `habit shell-install [--remove]` | Add or remove `~/.zshrc` hook |

---

## TUI keybindings

| Key | Action |
|-----|--------|
| `d` | Mark today done |
| `u` | Undo today |
| `a` | Add new habit |
| `x` | Delete selected habit |
| `1` / `2` / `3` | Year / quarter / month range |
| `j` / `↓` | Move down |
| `k` / `↑` | Move up |
| `q` | Quit |

---

## Shell startup hook

Once the app works to your satisfaction:

```bash
habit shell-install
```

Appends an idempotent block to `~/.zshrc` that runs `habit summary` on every interactive terminal open. Only runs when the terminal is interactive and `habit` is on PATH — never produces errors.

Remove with:

```bash
habit shell-install --remove
```

---

## Configuration

Create `~/.config/habit-tracker/config.toml` to override defaults:

```toml
default_range = "year"   # year | quarter | month
week_start    = "sunday" # sunday | monday
theme         = "github" # github (only theme currently)
```

---

## Data storage

| Path | Purpose |
|------|---------|
| `~/.local/share/habit-tracker/habits.db` | SQLite database (WAL mode) |
| `~/.config/habit-tracker/config.toml` | Optional config overrides |

Back up with `habit export -o backup.json`. Restore with `habit import backup.json`.

---

## Development

```bash
git clone https://github.com/Rohithn14/habit_tracker_cli.git
cd habit_tracker_cli
uv sync --group dev
uv run pytest        # 41 tests
uv run habit --help
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License

[MIT](LICENSE) © Rohithn14
