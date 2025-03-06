from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models import Appointment, Staff, Service, Branch, AppointmentStatus
from app.core.exceptions import AppointmentError

def appointment_to_dict(appointment: Appointment) -> Dict[str, Any]:
    return {
        "id": appointment.id,
        "customer_id": appointment.customer_id,
        "staff_id": appointment.staff_id,
        "service_id": appointment.service_id,
        "branch_id": appointment.branch_id,
        "appointment_time": appointment.appointment_time,
        "end_time": appointment.end_time,
        "status": appointment.status.value if appointment.status else None,
        "notes": appointment.notes
    }

class AppointmentService:
    def __init__(self, db: Session):
        self.db = db

    async def check_availability(
        self,
        branch_id: int,
        service_id: int,
        date: datetime,
        staff_id: Optional[int] = None
    ) -> List[datetime]:
        """
        Check available time slots for a given service at a branch
        """
        service = self.db.query(Service).filter(Service.id == service_id).first()
        if not service:
            raise AppointmentError("Service not found")

        # Get all appointments for the day
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        query = self.db.query(Appointment).filter(
            Appointment.branch_id == branch_id,
            Appointment.service_id == service_id,
            Appointment.appointment_time >= start_of_day,
            Appointment.appointment_time < end_of_day,
            Appointment.status != AppointmentStatus.CANCELLED
        )

        if staff_id:
            query = query.filter(Appointment.staff_id == staff_id)

        existing_appointments = query.all()

        # Generate available time slots
        available_slots = []
        current_time = start_of_day + timedelta(hours=9)  # Assuming business hours start at 9 AM
        end_time = start_of_day + timedelta(hours=17)  # Assuming business hours end at 5 PM

        while current_time < end_time:
            slot_end = current_time + timedelta(minutes=service.duration_minutes)
            if slot_end > end_time:
                break

            # Check if slot is available
            is_available = True
            for appointment in existing_appointments:
                if (current_time < appointment.end_time and 
                    slot_end > appointment.appointment_time):
                    is_available = False
                    break

            if is_available:
                available_slots.append(current_time)

            current_time += timedelta(minutes=30)  # 30-minute intervals

        return available_slots

    async def create_appointment(
        self,
        customer_id: int,
        staff_id: int,
        service_id: int,
        branch_id: int,
        appointment_time: datetime,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new appointment
        """
        # Check if the slot is available
        available_slots = await self.check_availability(
            branch_id=branch_id,
            service_id=service_id,
            date=appointment_time,
            staff_id=staff_id
        )

        if appointment_time not in available_slots:
            raise AppointmentError("Selected time slot is not available")

        service = self.db.query(Service).filter(Service.id == service_id).first()
        end_time = appointment_time + timedelta(minutes=service.duration_minutes)

        appointment = Appointment(
            customer_id=customer_id,
            staff_id=staff_id,
            service_id=service_id,
            branch_id=branch_id,
            appointment_time=appointment_time,
            end_time=end_time,
            notes=notes,
            status=AppointmentStatus.SCHEDULED
        )

        self.db.add(appointment)
        self.db.commit()
        self.db.refresh(appointment)

        return appointment_to_dict(appointment)

    async def cancel_appointment(self, appointment_id: int) -> Dict[str, Any]:
        """
        Cancel an appointment
        """
        appointment = self.db.query(Appointment).filter(
            Appointment.id == appointment_id
        ).first()

        if not appointment:
            raise AppointmentError("Appointment not found")

        if appointment.status == AppointmentStatus.CANCELLED:
            raise AppointmentError("Appointment is already cancelled")

        appointment.status = AppointmentStatus.CANCELLED
        self.db.commit()
        self.db.refresh(appointment)

        return appointment_to_dict(appointment)

    async def get_appointment(self, appointment_id: int) -> Dict[str, Any]:
        """
        Get appointment details
        """
        appointment = self.db.query(Appointment).filter(
            Appointment.id == appointment_id
        ).first()

        if not appointment:
            raise AppointmentError("Appointment not found")

        return appointment_to_dict(appointment)

    async def get_customer_appointments(
        self,
        customer_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all appointments, optionally filtered by customer and date range
        """
        query = self.db.query(Appointment)

        if customer_id:
            query = query.filter(Appointment.customer_id == customer_id)
        if start_date:
            query = query.filter(Appointment.appointment_time >= start_date)
        if end_date:
            query = query.filter(Appointment.appointment_time <= end_date)

        appointments = query.order_by(Appointment.appointment_time).all()
        return [appointment_to_dict(appointment) for appointment in appointments] 