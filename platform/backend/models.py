"""Database models for the platform."""

import enum
from datetime import datetime

import bcrypt

from .database import db


class FindingStatus(enum.IntEnum):
    """Status of a finding."""

    OPEN = 0
    INVESTIGATING = 1
    CLOSED = 2


class FindingType(enum.IntEnum):
    """Type of a finding."""

    IMAGING = 0
    HANDOFF = 1


class User(db.Model):
    """User model for authentication and user management."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    first_name = db.Column(db.String(80), nullable=True)
    last_name = db.Column(db.String(80), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self):
        return f"<User {self.username}>"

    def set_password(self, password: str, rounds: int = 12) -> None:
        """Hash and set the user's password."""
        salt = bcrypt.gensalt(rounds=rounds)
        self.password_hash = bcrypt.hashpw(password.encode("utf-8"), salt).decode(
            "utf-8"
        )

    def check_password(self, password: str) -> bool:
        """Check if the provided password matches the stored hash."""
        return bcrypt.checkpw(
            password.encode("utf-8"), self.password_hash.encode("utf-8")
        )

    def to_dict(self) -> dict:
        """Convert user to dictionary (excluding password)."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "is_active": self.is_active,
            "is_admin": self.is_admin,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Report(db.Model):
    """Report model for tracking findings."""

    __tablename__ = "reports"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.String(100), nullable=False, index=True)
    date_of_finding = db.Column(db.Date, nullable=False)
    status = db.Column(db.Integer, nullable=False, default=FindingStatus.OPEN)
    finding_type = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self):
        return f"<Report {self.id} - Patient {self.patient_id}>"

    @property
    def status_enum(self) -> FindingStatus:
        """Get status as enum."""
        return FindingStatus(self.status)

    @property
    def finding_type_enum(self) -> FindingType:
        """Get finding_type as enum."""
        return FindingType(self.finding_type)

    def to_dict(self) -> dict:
        """Convert report to dictionary."""
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "date_of_finding": (
                self.date_of_finding.isoformat() if self.date_of_finding else None
            ),
            "status": self.status_enum.name,
            "finding_type": self.finding_type_enum.name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
