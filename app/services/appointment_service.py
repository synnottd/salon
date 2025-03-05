from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.models import Appointment, Staff, Service, Branch, AppointmentStatus
from app.core.exceptions import AppointmentError

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
            Appointment.start_time >= start_of_day,
            Appointment.start_time < end_of_day,
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
                    slot_end > appointment.start_time):
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
        start_time: datetime,
        notes: Optional[str] = None
    ) -> Appointment:
        """
        Create a new appointment
        """
        # Check if the slot is available
        available_slots = await self.check_availability(
            branch_id=branch_id,
            service_id=service_id,
            date=start_time,
            staff_id=staff_id
        )

        if start_time not in available_slots:
            raise AppointmentError("Selected time slot is not available")

        service = self.db.query(Service).filter(Service.id == service_id).first()
        end_time = start_time + timedelta(minutes=service.duration_minutes)

        appointment = Appointment(
            customer_id=customer_id,
            staff_id=staff_id,
            service_id=service_id,
            branch_id=branch_id,
            start_time=start_time,
            end_time=end_time,
            notes=notes,
            status=AppointmentStatus.PENDING
        )

        self.db.add(appointment)
        self.db.commit()
        self.db.refresh(appointment)

        return appointment

    async def cancel_appointment(self, appointment_id: int, customer_id: int) -> Appointment:
        """
        Cancel an appointment
        """
        appointment = self.db.query(Appointment).filter(
            Appointment.id == appointment_id,
            Appointment.customer_id == customer_id
        ).first()

        if not appointment:
            raise AppointmentError("Appointment not found")

        if appointment.status == AppointmentStatus.CANCELLED:
            raise AppointmentError("Appointment is already cancelled")

        appointment.status = AppointmentStatus.CANCELLED
        self.db.commit()
        self.db.refresh(appointment)

        return appointment

    async def get_appointment(self, appointment_id: int, customer_id: int) -> Appointment:
        """
        Get appointment details
        """
        appointment = self.db.query(Appointment).filter(
            Appointment.id == appointment_id,
            Appointment.customer_id == customer_id
        ).first()

        if not appointment:
            raise AppointmentError("Appointment not found")

        return appointment

    async def get_customer_appointments(
        self,
        customer_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Appointment]:
        """
        Get all appointments for a customer within a date range
        """
        query = self.db.query(Appointment).filter(
            Appointment.customer_id == customer_id
        )

        if start_date:
            query = query.filter(Appointment.start_time >= start_date)
        if end_date:
            query = query.filter(Appointment.start_time <= end_date)

        return query.order_by(Appointment.start_time).all() 