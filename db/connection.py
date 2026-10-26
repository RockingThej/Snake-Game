"""SQLite path selection, connections, and idempotent first-run setup."""
import os
from pathlib import Path
import sqlite3

from db.schema import SCHEMA, TABLE_NAMES


def _default_db_path():
    configured_path = os.environ.get("SNAKE_GAME_DB_PATH")
    if configured_path:
        return Path(configured_path).expanduser()

    app_data = os.environ.get("LOCALAPPDATA")
    if app_data:
        return Path(app_data) / "SnakeGame" / "snake_game.sqlite3"
    return (
        Path.home() / ".local" / "share" / "snake-game" / "snake_game.sqlite3"
    )


DEFAULT_DB_PATH = _default_db_path()


def _open_connection(db_path):
    connection = sqlite3.connect(str(db_path), timeout=5.0)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(db_path=None):
    """Create the database and its tables if they do not already exist.

    The default database lives in the user's local application data directory.
    ``db_path`` can be provided by tests or callers needing a separate
    database.
    """
    path = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
    path = path.expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = _open_connection(path)
    try:
        connection.executescript(SCHEMA)
        connection.commit()
    finally:
        connection.close()
    return path


def get_connection(db_path=None):
    """Return a connection after ensuring the schema is initialized."""
    path = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
    path = initialize_database(path)
    return _open_connection(path)


def get_table_names(db_path=None):
    """Return the required application tables (useful for health checks)."""
    connection = get_connection(db_path)
    try:
        rows = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
        existing = {row["name"] for row in rows}
        return tuple(name for name in TABLE_NAMES if name in existing)
    finally:
        connection.close()
