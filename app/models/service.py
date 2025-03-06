from sqlalchemy import Column, String, Integer, Float
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class Service(BaseModel):
    __tablename__ = "services"

    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(500))
    duration_minutes = Column(Integer, nullable=False)  # Duration in minutes
    price = Column(Float, nullable=False)
    category = Column(String(50))  # e.g., "Hair", "Nails", "Facial", etc.

    # Relationships
    appointments = relationship("Appointment", back_populates="service") 