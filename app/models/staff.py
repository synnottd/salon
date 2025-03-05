from sqlalchemy import Column, String, ForeignKey, Boolean, Integer
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class Staff(BaseModel):
    __tablename__ = "staff"

    name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    phone = Column(String(20))
    role = Column(String(50), nullable=False)
    branch_id = Column(Integer, ForeignKey('branches.id'), nullable=False)
    is_active = Column(Boolean, default=True)
    specialties = Column(String(255))  # Comma-separated list of services they can provide

    # Relationships
    branch = relationship("Branch", back_populates="staff")
    appointments = relationship("Appointment", back_populates="staff") 