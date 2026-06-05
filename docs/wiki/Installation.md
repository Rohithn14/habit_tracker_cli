# Installation

## Requirements

- Python 3.11 or later
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

## Recommended: uv tool install

`uv tool install` puts `habit` in an isolated environment and on your `PATH` — no virtualenv management needed.

```bash
# From PyPI (once published)
uv tool install habit-tracker

# From GitHub directly
uv tool install git+https://github.com/Rohithn14/habit_tracker_cli.git
```

Verify:

```bash
habit --help
```

## pip

```bash
pip install habit-tracker
```

## From source

```bash
git clone https://github.com/Rohithn14/habit_tracker_cli.git
cd habit_tracker_cli
uv tool install .
```

Or for active development (editable, no PATH install):

```bash
uv sync --group dev
uv run habit --help
```

## Upgrading

```bash
uv tool upgrade habit-tracker
```

## Uninstalling

```bash
uv tool uninstall habit-tracker
habit shell-install --remove   # also remove the ~/.zshrc hook if installed
```
