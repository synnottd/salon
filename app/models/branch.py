from sqlalchemy import Column, String, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class Branch(BaseModel):
    __tablename__ = "branches"

    name = Column(String(100), nullable=False)
    address = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(2), nullable=False)  # Two-letter state code
    phone = Column(String(20), nullable=False)
    email = Column(String(255))
    description = Column(Text)
    opening_hours = Column(String(255))  # JSON string of opening hours

    # Relationships
    staff = relationship("Staff", back_populates="branch")
    appointments = relationship("Appointment", back_populates="branch") 