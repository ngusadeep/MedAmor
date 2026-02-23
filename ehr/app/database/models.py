"""Database models for EHR service."""

from sqlalchemy import Column, String, Text
from sqlalchemy.orm import Mapped

from .connection import Base


class Patient(Base):
    """Patient record sourced from a FHIR R4 bundle."""

    __tablename__ = "patients"

    patient_id: Mapped[str] = Column(String, primary_key=True, index=True)
    patient_name: Mapped[str | None] = Column(String, nullable=True)

    # Demographics extracted from FHIR Patient resource
    birth_date: Mapped[str | None] = Column(String, nullable=True)
    gender: Mapped[str | None] = Column(String, nullable=True)
    address: Mapped[str | None] = Column(String, nullable=True)
    phone: Mapped[str | None] = Column(String, nullable=True)
    race: Mapped[str | None] = Column(String, nullable=True)
    ethnicity: Mapped[str | None] = Column(String, nullable=True)
    marital_status: Mapped[str | None] = Column(String, nullable=True)

    # Raw FHIR R4 bundle (JSON string) — source of truth
    fhir_json: Mapped[str | None] = Column(Text, nullable=True)

    # Timeline text generated from fhir_json; populated lazily on first audit request
    timeline_cache: Mapped[str | None] = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Patient(id={self.patient_id}, name={self.patient_name})>"
