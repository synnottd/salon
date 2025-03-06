from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import BaseModel

class Customer(BaseModel):
    __tablename__ = "customers"

    name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    phone = Column(String(20))
    preferences = Column(Text)

    # Relationships
    appointments = relationship("Appointment", back_populates="customer") 