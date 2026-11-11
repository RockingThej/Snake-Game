"""Optional schema extensions, one file per feature.

Every module named ``db/ext_*.py`` may define a ``SQL`` string made of
idempotent statements (``CREATE TABLE IF NOT EXISTS ...``). They are applied
after the core schema in ``db/schema.py`` each time the database is
initialised. Keeping each feature's tables in its own file means features can
be developed in parallel without editing the shared ``SCHEMA`` string.
"""
import importlib
from pathlib import Path

_PREFIX = "ext_"


def extension_names():
    """Return the dotted module names of all schema extensions, sorted."""
    folder = Path(__file__).resolve().parent
    return sorted(
        "db.%s" % path.stem for path in folder.glob(_PREFIX + "*.py")
    )


def apply_extensions(connection):
    """Run the SQL of every ``db/ext_*.py`` module on ``connection``."""
    for name in extension_names():
        module = importlib.import_module(name)
        sql = getattr(module, "SQL", None)
        if sql:
            connection.executescript(sql)
