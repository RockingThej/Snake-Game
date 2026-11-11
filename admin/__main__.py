"""Command line for the first-time setup of administrators.

There is no way to become an administrator from inside the game, so the
very first one is created by whoever has access to the machine:

    python -m admin make-admin alice
    python -m admin list-users
    python -m admin remove-admin alice
    python -m admin --db path/to/other.sqlite3 list-users
"""
import argparse
import sys

from db import admin_repository as repo
from db import get_user_by_username


def _build_parser():
    parser = argparse.ArgumentParser(
        prog="python -m admin", description=__doc__.split("\n\n")[0])
    parser.add_argument("--db", default=None,
                        help="path to the SQLite database (default: the "
                             "game's normal database)")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list-users", help="show all accounts")
    for name, text in (("make-admin", "make an existing user an admin"),
                       ("remove-admin", "remove admin rights from a user")):
        sub = commands.add_parser(name, help=text)
        sub.add_argument("username")
    return parser


def main(argv=None, out=None):
    out = out or sys.stdout
    args = _build_parser().parse_args(argv)

    if args.command == "list-users":
        for user in repo.list_users(limit=1000, db_path=args.db):
            flags = ", ".join(
                flag for flag, on in (("admin", user["is_admin"]),
                                      ("disabled", user["disabled"])) if on)
            print("%4d  %-20s %s" % (user["id"], user["username"], flags),
                  file=out)
        return 0

    user = get_user_by_username(args.username.strip(), db_path=args.db)
    if user is None:
        print("No such user: %s" % args.username, file=out)
        return 1

    if args.command == "make-admin":
        changed = repo.add_admin(user["id"], granted_by=None,
                                 db_path=args.db)
        action, done = "cli_make_admin", "is now an administrator"
        if not changed:
            print("%s already is an administrator" % user["username"],
                  file=out)
            return 0
    else:
        if repo.count_admins(db_path=args.db) <= 1 and repo.is_admin(
                user["id"], db_path=args.db):
            print("Refusing to remove the last administrator", file=out)
            return 1
        if not repo.remove_admin(user["id"], db_path=args.db):
            print("%s is not an administrator" % user["username"], file=out)
            return 0
        action, done = "cli_remove_admin", "is no longer an administrator"

    repo.add_audit_entry(None, "cli", action,
                         "user:%d:%s" % (user["id"], user["username"]),
                         db_path=args.db)
    print("%s %s" % (user["username"], done), file=out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
