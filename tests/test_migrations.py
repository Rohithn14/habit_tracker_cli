"""Tests for the migration framework (storage.py) and config validation."""
import sqlite3

import pytest

import habit_tracker.config as config
from habit_tracker import storage
from habit_tracker.storage import _MIGRATIONS, init_db


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    db_path = tmp_path / "habits.db"
    monkeypatch.setattr("habit_tracker.storage.DB_PATH", db_path)
    monkeypatch.setattr("habit_tracker.config.DATA_DIR", tmp_path)
    monkeypatch.setattr("habit_tracker.config.CONFIG_DIR", tmp_path)
    monkeypatch.setattr("habit_tracker.config.CONFIG_PATH", tmp_path / "config.toml")
    yield db_path


def _user_version() -> int:
    with storage._conn() as con:
        return con.execute("PRAGMA user_version").fetchone()[0]


class TestMigrations:
    def test_fresh_db_reaches_latest_version(self):
        init_db()
        assert _user_version() == len(_MIGRATIONS)

    def test_init_db_is_idempotent(self):
        init_db()
        v1 = _user_version()
        init_db()  # second run must be a no-op
        assert _user_version() == v1 == len(_MIGRATIONS)

    def test_legacy_db_upgrades_cleanly(self, isolated_db):
        # Simulate a pre-migration DB: schema present but user_version still 0.
        with storage._conn() as con:
            con.executescript(storage._SCHEMA)
            con.execute("ALTER TABLE entries ADD COLUMN notes TEXT")
            assert con.execute("PRAGMA user_version").fetchone()[0] == 0
        init_db()
        assert _user_version() == len(_MIGRATIONS)

    def test_schema_has_expected_tables(self):
        init_db()
        with storage._conn() as con:
            tables = {r[0] for r in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )}
        assert {"habits", "entries"} <= tables


class TestConfigValidation:
    def test_clamps_invalid_values_to_defaults(self):
        out = config.validate_config({"default_range": "decade", "week_start": "tuesday"})
        assert out["default_range"] == "year"
        assert out["week_start"] == "sunday"

    def test_keeps_valid_values(self):
        out = config.validate_config({"default_range": "month", "week_start": "monday"})
        assert out["default_range"] == "month"
        assert out["week_start"] == "monday"

    def test_drops_unknown_keys(self):
        out = config.validate_config({"bogus": 123})
        assert "bogus" not in out

    def test_save_load_round_trip(self):
        config.save_config({"default_range": "quarter", "week_start": "monday"})
        loaded = config.load_config()
        assert loaded["default_range"] == "quarter"
        assert loaded["week_start"] == "monday"

    def test_save_sanitizes_before_writing(self):
        config.save_config({"default_range": "nonsense"})
        assert config.load_config()["default_range"] == "year"
