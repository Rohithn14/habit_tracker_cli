# CLI Reference

All commands follow `habit <command> [OPTIONS] [ARGS]`. Run `habit <command> --help` for full flag details.

---

## `habit add`

Create a new habit.

```
habit add NAME [--emoji E] [--target N] [--color C]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--emoji`, `-e` | — | Emoji prefix shown in list and TUI |
| `--target`, `-t` | none | Daily count target (drives intensity shading) |
| `--color`, `-c` | `green` | Accent color name |

```bash
habit add "Morning Run" --emoji 🏃 --target 3
habit add "Meditate"    --emoji 🧘
```

---

## `habit done`

Log a day as done (upserts — safe to run multiple times with different counts).

```
habit done NAME [--date YYYY-MM-DD] [--count N]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--date`, `-d` | today | ISO date to log |
| `--count`, `-n` | 1 | Count for that day |

```bash
habit done "Morning Run"
habit done "Morning Run" --count 2
habit done "Morning Run" --date 2026-06-01 --count 3
```

---

## `habit undo`

Remove a logged entry for a single day or a date range.

```
habit undo NAME [--date YYYY-MM-DD]
habit undo NAME --from YYYY-MM-DD --to YYYY-MM-DD
```

| Flag | Description |
|------|-------------|
| `--date`, `-d` | Single date to remove (default: today) |
| `--from` | Start of range to remove |
| `--to` | End of range to remove (inclusive) |

```bash
habit undo "Morning Run"                                    # removes today
habit undo "Morning Run" --date 2026-06-01
habit undo "Morning Run" --from 2026-06-01 --to 2026-06-07 # removes a whole week
```

---

## `habit list`

List all active habits with streak and today status.

```
habit list [--all]
```

`--all` includes archived habits.

---

## `habit show`

Render the heatmap and stats panel for one habit.

```
habit show NAME [--range year|quarter|month]
```

```bash
habit show "Morning Run" --range quarter
```

---

## `habit summary`

Compact one-line-per-habit view (used by the shell startup hook).

```
habit summary [--range year|quarter|month]
```

Exits silently with code 0 even when the database is missing — safe for shell startup.

---

## `habit rm`

Remove or archive a habit and all its entries.

```
habit rm NAME [--archive] [--force]
```

| Flag | Description |
|------|-------------|
| `--archive` | Soft-delete: hides from list but keeps data |
| `--force` | Skip confirmation prompt |

---

## `habit note`

Attach a text note to a habit entry (creates the entry if it doesn't exist yet).

```
habit note NAME TEXT [--date YYYY-MM-DD]
```

```bash
habit note "Morning Run" "felt strong today"
habit note "Morning Run" "skipped — rain" --date 2026-06-01
```

Notes are visible in the TUI by clicking the corresponding heatmap cell (violet `•` marks cells that have a note).

---

## `habit export`

Export all habits and entries to JSON or CSV.

```
habit export [-o FILE] [--format json|csv]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--output`, `-o` | stdout | Output file path |
| `--format`, `-f` | `json` | Export format: `json` or `csv` |

```bash
habit export -o backup.json                # JSON (default)
habit export --format csv -o habits.csv    # flat CSV
habit export | jq .                        # JSON to stdout
```

---

## `habit import`

Import from a JSON export.

```
habit import FILE [--overwrite]
```

Without `--overwrite`, existing entries for a date are skipped (safe to re-import).

---

## `habit tui`

Launch the [interactive TUI](TUI-Guide).

```bash
habit tui
```

---

## `habit shell-install`

Add or remove the `~/.zshrc` startup hook.

```bash
habit shell-install           # install
habit shell-install --remove  # remove
```

See [Shell Integration](Shell-Integration) for details.
