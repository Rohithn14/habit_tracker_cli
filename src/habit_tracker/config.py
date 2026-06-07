from __future__ import annotations

import sys
import tomllib
from pathlib import Path

from platformdirs import user_config_dir, user_data_dir

APP_NAME = "habit-tracker"

DATA_DIR = Path(user_data_dir(APP_NAME))
CONFIG_DIR = Path(user_config_dir(APP_NAME))
DB_PATH = DATA_DIR / "habits.db"
CONFIG_PATH = CONFIG_DIR / "config.toml"

_DEFAULTS: dict = {
    "default_range": "year",
    "week_start": "sunday",
    "theme": "github",
}

# Allowed values per known key; keys absent here pass through unchanged.
_ALLOWED: dict[str, set[str]] = {
    "default_range": {"year", "quarter", "month"},
    "week_start": {"sunday", "monday"},
}


def validate_config(cfg: dict) -> dict:
    """Return a sanitized config: known keys clamped to allowed values (falling back
    to the default when invalid), unknown keys dropped."""
    out = dict(_DEFAULTS)
    for key, default in _DEFAULTS.items():
        if key not in cfg:
            continue
        value = cfg[key]
        allowed = _ALLOWED.get(key)
        out[key] = value if (allowed is None or value in allowed) else default
    return out


def load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "rb") as f:
            user = tomllib.load(f)
        return validate_config({**_DEFAULTS, **user})
    return dict(_DEFAULTS)


def save_config(cfg: dict) -> None:
    """Validate and persist config to CONFIG_PATH as TOML."""
    import tomli_w

    ensure_dirs()
    with open(CONFIG_PATH, "wb") as f:
        tomli_w.dump(validate_config(cfg), f)


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
