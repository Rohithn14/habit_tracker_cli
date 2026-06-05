# Data Export & Import

## Exporting

Export all habits and entries to a JSON file:

```bash
habit export -o backup.json
```

Or print to stdout (useful for piping):

```bash
habit export | jq .
```

### Format

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
      { "date": "2026-06-01", "count": 2 },
      { "date": "2026-06-02", "count": 3 }
    ]
  }
]
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
