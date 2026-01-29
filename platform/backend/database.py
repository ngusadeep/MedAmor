"""Database setup and session management."""

from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy instance
db = SQLAlchemy()


def init_db(app):
    """Initialize the database with the Flask app."""
    db.init_app(app)
