"""Database models for EHR service."""

from sqlalchemy import Column, String, Text
from sqlalchemy.orm import Mapped

from .connection import Base


class Patient(Base):
    """Patient model matching backend EHR expectations."""

    __tablename__ = "patients"

    patient_id: Mapped[str] = Column(String, primary_key=True, index=True)
    patient_name: Mapped[str | None] = Column(String, nullable=True)
    ehr_text: Mapped[str] = Column(Text, nullable=False)

    def __repr__(self):
        return f"<Patient(patient_id={self.patient_id}, patient_name={self.patient_name})>"