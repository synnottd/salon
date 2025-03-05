from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from app.db.session import get_db
from app.services.appointment_service import AppointmentService
from app.models import Appointment, AppointmentStatus
from pydantic import BaseModel

router = APIRouter()

class AppointmentCreate(BaseModel):
    customer_id: int
    staff_id: int
    service_id: int
    branch_id: int
    appointment_time: datetime
    notes: Optional[str] = None

class AppointmentResponse(BaseModel):
    id: int
    customer_id: int
    staff_id: int
    service_id: int
    branch_id: int
    appointment_time: datetime
    end_time: datetime
    status: str
    notes: Optional[str] = None

@router.post("/", response_model=AppointmentResponse)
async def create_appointment(
    appointment: AppointmentCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new appointment
    """
    appointment_service = AppointmentService(db)
    return await appointment_service.create_appointment(
        customer_id=appointment.customer_id,
        staff_id=appointment.staff_id,
        service_id=appointment.service_id,
        branch_id=appointment.branch_id,
        appointment_time=appointment.appointment_time,
        notes=appointment.notes
    )

@router.get("/", response_model=List[AppointmentResponse])
async def get_appointments(
    customer_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """
    Get all appointments, optionally filtered by customer
    """
    appointment_service = AppointmentService(db)
    return await appointment_service.get_customer_appointments(
        customer_id=customer_id,
        start_date=start_date,
        end_date=end_date
    )

@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific appointment
    """
    appointment_service = AppointmentService(db)
    return await appointment_service.get_appointment(
        appointment_id=appointment_id
    )

@router.post("/{appointment_id}/cancel", response_model=AppointmentResponse)
async def cancel_appointment(
    appointment_id: int,
    db: Session = Depends(get_db)
):
    """
    Cancel an appointment
    """
    appointment_service = AppointmentService(db)
    return await appointment_service.cancel_appointment(
        appointment_id=appointment_id
    )

@router.get("/availability")
async def check_availability(
    branch_id: int,
    service_id: int,
    date: datetime,
    staff_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Check available time slots for a service
    """
    appointment_service = AppointmentService(db)
    return await appointment_service.check_availability(
        branch_id=branch_id,
        service_id=service_id,
        date=date,
        staff_id=staff_id
    ) 