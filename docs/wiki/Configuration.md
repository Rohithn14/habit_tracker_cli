# Configuration

habit-tracker reads an optional TOML config file at:

```
~/.config/habit-tracker/config.toml
```

The file is created automatically on first use (empty; all keys are optional).

## Available keys

```toml
# Default time range for `habit show` and `habit summary`
# Options: "year" | "quarter" | "month"
default_range = "year"

# Which day starts the week in the heatmap grid
# Options: "sunday" | "monday"
week_start = "sunday"

# Color theme
# Options: "github"  (only one currently)
theme = "github"
```

## Defaults

| Key | Default |
|-----|---------|
| `default_range` | `"year"` |
| `week_start` | `"sunday"` |
| `theme` | `"github"` |

## Example

```toml
default_range = "quarter"
week_start    = "monday"
```

## Data directory

The SQLite database lives at:

```
~/.local/share/habit-tracker/habits.db
```

Both paths follow the [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html) via `platformdirs`.
