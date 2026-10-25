"""S1-14 Registration (bcrypt) and S1-15 Authentication / session handling."""
import functools
import sqlite3

import bcrypt
from flask import Blueprint, g, jsonify, request, session

from .db import get_db
from .validators import (ValidationError, validate_email, validate_password,
                         validate_username)

bp = Blueprint("auth", __name__, url_prefix="/api/auth")

# Used to keep login timing similar whether or not the user exists.
_DUMMY_HASH = bcrypt.hashpw(b"dummy-password", bcrypt.gensalt())


# ---------- password helpers ----------
def hash_password(password: str) -> bytes:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())


def check_password(password: str, password_hash: bytes) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash)
    except ValueError:
        return False


# ---------- session helpers ----------
@bp.before_app_request
def load_logged_in_user():
    user_id = session.get("user_id")
    g.user = None
    if user_id is not None:
        row = get_db().execute(
            "SELECT id, username, email FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        g.user = dict(row) if row else None
        if g.user is None:
            session.clear()


def login_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if g.get("user") is None:
            return jsonify(error="Authentication required."), 401
        return view(*args, **kwargs)
    return wrapped


@bp.errorhandler(ValidationError)
def handle_validation_error(err):
    return jsonify(error=err.message, field=err.field), 400


# ---------- routes ----------
@bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    username = validate_username(data.get("username"))
    email = validate_email(data.get("email"))
    password = validate_password(data.get("password"))

    db = get_db()
    try:
        cur = db.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, hash_password(password)),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify(error="Username or email already in use."), 409

    return jsonify(id=cur.lastrowid, username=username, email=email), 201


@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    identifier = data.get("username")
    password = data.get("password")
    if not isinstance(identifier, str) or not isinstance(password, str):
        return jsonify(error="Username and password are required."), 400

    row = get_db().execute(
        "SELECT id, username, password_hash FROM users "
        "WHERE username = ? OR email = ?",
        (identifier.strip(), identifier.strip().lower()),
    ).fetchone()

    stored = row["password_hash"] if row else _DUMMY_HASH
    ok = check_password(password, stored)
    if not row or not ok:
        # Same message for both cases: don't reveal which usernames exist.
        return jsonify(error="Invalid username or password."), 401

    session.clear()  # prevents session fixation
    session["user_id"] = row["id"]
    session.permanent = True
    return jsonify(id=row["id"], username=row["username"])


@bp.post("/logout")
def logout():
    session.clear()
    return jsonify(message="Logged out."), 200


@bp.get("/me")
@login_required
def me():
    return jsonify(g.user)
