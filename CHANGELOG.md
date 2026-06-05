# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.1.0] - 2026-06-05

### Added
- GitHub-style contribution heatmap rendered in the terminal (7 weekday rows × week columns, 5-shade green palette)
- Intensity shading: 5 buckets keyed to fraction of a per-habit daily target
- Stats panel: current streak, longest streak, completion rate, total completions, today status
- Time ranges: year, quarter, month — switchable via `--range` flag or TUI keypresses
- CLI commands: `add`, `done`, `undo`, `list`, `show`, `summary`, `rm`, `export`, `import`, `tui`, `shell-install`
- Interactive Textual TUI with habit sidebar, heatmap + stats detail pane, full keybinding set
- Compact startup summary: one sparkline row per habit shown on terminal open
- Shell hook installer: `habit shell-install` idempotently manages a marked block in `~/.zshrc`
- SQLite storage with WAL mode, foreign-key cascade, upsert via `ON CONFLICT`
- JSON export/import for backup and portability
- `py.typed` marker for type-checker support
- 41 unit + integration tests (stats logic + storage CRUD)
