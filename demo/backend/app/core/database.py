"""Database engine and session; create tables on init."""

from collections.abc import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    echo=settings.debug and settings.environment == "development",
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db() -> None:
    """Create all tables. Call once on startup."""
    from app.models import audit_report, job, report_annotation, user  # noqa: F401
    from app.models.user import UserRole

    Base.metadata.create_all(bind=engine)

    # Create default users and migrate existing ones
    db = SessionLocal()
    try:
        from app.models.user import User
        from app.core.security import hash_password

        # Update users with NULL role to DOCTOR
        db.query(User).filter(User.role.is_(None)).update({"role": UserRole.DOCTOR})
        db.commit()

        # Create default Chief Doctor user
        chief_doctor = (
            db.query(User).filter(User.username == "chief@medarmor.com").first()
        )
        if not chief_doctor:
            chief_doctor = User(
                username="chief@medarmor.com",
                hashed_password=hash_password("chief123"),
                role=UserRole.CHIEF_DOCTOR,
            )
            db.add(chief_doctor)
            db.commit()

        # Create default Doctor user
        doctor = db.query(User).filter(User.username == "doctor@medarmor.com").first()
        if not doctor:
            doctor = User(
                username="doctor@medarmor.com",
                hashed_password=hash_password("doctor123"),
                role=UserRole.DOCTOR,
            )
            db.add(doctor)
            db.commit()

    except Exception:
        # Ignore if table doesn't exist yet or other errors
        db.rollback()
    finally:
        db.close()


def get_db_session() -> Generator[Session, None, None]:
    """FastAPI dependency: yield a DB session; caller commits or rollback."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
