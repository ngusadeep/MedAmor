"""
Startup tasks run automatically on app/container start.

- Migrations are run from start.sh (alembic upgrade head).
- This module ensures default admin user exists (skips if user/tables already exist).
"""

import os
import sys

from .app import create_app
from .database import db
from .models import User


def ensure_default_user() -> bool:
    """
    Create default admin user from env vars if not already present.
    Skips if DEFAULT_ADMIN_USERNAME/EMAIL/PASSWORD are not set, or user already exists.
    Returns True if user was created, False if skipped.
    """
    username = os.environ.get("DEFAULT_ADMIN_USERNAME")
    email = os.environ.get("DEFAULT_ADMIN_EMAIL")
    password = os.environ.get("DEFAULT_ADMIN_PASSWORD")

    if not username or not email or not password:
        return False

    app = create_app()
    with app.app_context():
        if User.query.filter_by(username=username).first():
            return False
        if User.query.filter_by(email=email).first():
            return False

        user = User(
            username=username,
            email=email,
            first_name=os.environ.get("DEFAULT_ADMIN_FIRST_NAME", "Admin"),
            last_name=os.environ.get("DEFAULT_ADMIN_LAST_NAME", "User"),
            is_admin=True,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return True

    return False


def run_startup() -> None:
    """Run all startup tasks. Idempotent: safe to run on every container start."""
    try:
        if ensure_default_user():
            print("[startup] Default admin user created.")
        else:
            print(
                "[startup] Default admin user skipped (already exists or env not set)."
            )
    except Exception as e:
        # Don't fail container start; tables might not exist yet (migrations just ran)
        print(f"[startup] Warning: could not ensure default user: {e}", file=sys.stderr)


if __name__ == "__main__":
    run_startup()
