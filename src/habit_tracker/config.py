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


def load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "rb") as f:
            user = tomllib.load(f)
        return {**_DEFAULTS, **user}
    return dict(_DEFAULTS)


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
