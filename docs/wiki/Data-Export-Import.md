# Data Export & Import

## Exporting

Export all habits and entries to a JSON file (default) or flat CSV:

```bash
habit export -o backup.json               # JSON
habit export --format csv -o habits.csv   # CSV
habit export | jq .                       # JSON to stdout
```

### JSON format

```json
[
  {
    "name": "Morning Run",
    "emoji": "🏃",
    "color": "green",
    "target": 3,
    "created_at": "2026-01-01",
    "archived": false,
    "entries": [
      { "date": "2026-06-01", "count": 2, "notes": null },
      { "date": "2026-06-02", "count": 3, "notes": "felt great" }
    ]
  }
]
```

### CSV format

One row per entry, flat structure:

```
habit_name,emoji,target,date,count,notes
Morning Run,🏃,3,2026-06-01,2,
Morning Run,🏃,3,2026-06-02,3,felt great
```

## Importing

```bash
habit import backup.json
```

By default, existing entries for a date are **skipped** (safe to re-import without overwriting manual edits).

To overwrite existing entries:

```bash
habit import backup.json --overwrite
```

New habits in the file are created automatically. Existing habits (matched by name) are reused — no duplicates.

## Migration between machines

```bash
# On old machine
habit export -o backup.json

# Copy backup.json to new machine, then:
habit import backup.json
```

## Scheduled backups

```bash
# Add to cron or a shell alias
habit export -o ~/backups/habits-$(date +%Y%m%d).json
```
