"""Snake-Game backend: accounts, scoring and leaderboard."""
import os
from datetime import timedelta

from flask import Flask, jsonify

from . import db


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        # Override SECRET_KEY with an environment variable in production!
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-me"),
        DATABASE=os.path.join(app.instance_path, "snake.sqlite"),
        # Session hardening (S1-15)
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "0") == "1",
        PERMANENT_SESSION_LIFETIME=timedelta(hours=1),
    )
    if test_config:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)
    db.init_app(app)

    from .auth import bp as auth_bp
    from .scores import bp as scores_bp
    from .leaderboard import bp as leaderboard_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(scores_bp)
    app.register_blueprint(leaderboard_bp)

    @app.get("/health")
    def health():
        return jsonify(status="ok")

    return app
