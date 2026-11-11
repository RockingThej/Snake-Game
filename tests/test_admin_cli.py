"""S2-14: `python -m admin` for creating the first administrator."""
import io

import pytest

from admin.__main__ import main
from admin import AdminService
from db import create_user, initialize_database
from db import admin_repository as repo


@pytest.fixture()
def db_path(tmp_path):
    path = str(tmp_path / "cli.sqlite3")
    initialize_database(path)
    return path


def run(db_path, *args):
    out = io.StringIO()
    code = main(["--db", db_path, *args], out=out)
    return code, out.getvalue()


def test_make_admin_then_list(db_path):
    alice = create_user("alice", "h", db_path)
    create_user("bob", "h", db_path)

    code, text = run(db_path, "make-admin", "alice")
    assert code == 0 and "alice is now an administrator" in text
    assert repo.is_admin(alice, db_path=db_path)

    code, text = run(db_path, "list-users")
    assert code == 0
    assert "alice" in text and "admin" in text and "bob" in text


def test_the_new_admin_can_use_the_service(db_path):
    alice = create_user("alice", "h", db_path)
    run(db_path, "make-admin", "alice")
    assert AdminService(alice, db_path=db_path).list_users()


def test_make_admin_is_idempotent_and_audited(db_path):
    alice = create_user("alice", "h", db_path)
    run(db_path, "make-admin", "alice")
    code, text = run(db_path, "make-admin", "alice")
    assert code == 0 and "already" in text
    log = AdminService(alice, db_path=db_path).audit_log()
    assert [e["action"] for e in log] == ["cli_make_admin"]


def test_unknown_user(db_path):
    code, text = run(db_path, "make-admin", "ghost")
    assert code == 1 and "No such user" in text


def test_remove_admin_but_never_the_last_one(db_path):
    alice = create_user("alice", "h", db_path)
    bob = create_user("bob", "h", db_path)
    run(db_path, "make-admin", "alice")
    code, text = run(db_path, "remove-admin", "alice")
    assert code == 1 and "last administrator" in text
    assert repo.is_admin(alice, db_path=db_path)

    run(db_path, "make-admin", "bob")
    code, text = run(db_path, "remove-admin", "alice")
    assert code == 0 and "no longer" in text
    assert not repo.is_admin(alice, db_path=db_path)
    assert repo.is_admin(bob, db_path=db_path)


def test_remove_admin_from_a_normal_player(db_path):
    create_user("alice", "h", db_path)
    create_user("root", "h", db_path)
    run(db_path, "make-admin", "root")
    code, text = run(db_path, "remove-admin", "alice")
    assert code == 0 and "not an administrator" in text
