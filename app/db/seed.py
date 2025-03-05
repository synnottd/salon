from datetime import datetime, timedelta
import random
import json
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models import Branch, Staff, Appointment, AppointmentStatus, Customer, Service

# Sample data
SERVICES = [
    "Haircut", "Hair Coloring", "Highlights", "Blowout", "Hair Treatment",
    "Manicure", "Pedicure", "Facial", "Massage", "Waxing"
]

ROLES = ["Stylist", "Colorist", "Nail Technician", "Esthetician", "Massage Therapist"]

BRANCH_DATA = [
    {
        "name": "Downtown Salon",
        "address": "123 Main St, City Center",
        "phone": "555-0101",
        "email": "downtown@salon.com",
        "description": "Our flagship location in the heart of the city",
        "opening_hours": json.dumps({
            "Mon-Fri": "9:00-20:00",
            "Sat": "10:00-18:00",
            "Sun": "11:00-16:00"
        })
    },
    {
        "name": "Westside Beauty",
        "address": "456 West Ave, Westside",
        "phone": "555-0102",
        "email": "westside@salon.com",
        "description": "Luxury salon experience in the trendy Westside district",
        "opening_hours": json.dumps({
            "Mon-Fri": "9:00-20:00",
            "Sat": "10:00-18:00",
            "Sun": "Closed"
        })
    },
    {
        "name": "Eastside Style",
        "address": "789 East St, Eastside",
        "phone": "555-0103",
        "email": "eastside@salon.com",
        "description": "Modern salon with a traditional touch",
        "opening_hours": json.dumps({
            "Mon-Fri": "10:00-19:00",
            "Sat-Sun": "10:00-17:00"
        })
    },
    {
        "name": "North Station Salon",
        "address": "321 North Blvd, Northside",
        "phone": "555-0104",
        "email": "northside@salon.com",
        "description": "Contemporary salon near the transit hub",
        "opening_hours": json.dumps({
            "Mon-Sat": "9:00-19:00",
            "Sun": "Closed"
        })
    },
    {
        "name": "South Plaza Beauty",
        "address": "654 South Plaza, Southside",
        "phone": "555-0105",
        "email": "southside@salon.com",
        "description": "Family-friendly salon in South Plaza",
        "opening_hours": json.dumps({
            "Mon-Sun": "10:00-18:00"
        })
    }
]

def generate_phone():
    return f"555-{random.randint(1000,9999)}"

def generate_email(name):
    return f"{name.lower().replace(' ', '.')}@salon.com"

def create_test_data():
    try:
        db = SessionLocal()
        
        # Create services
        services = [
            Service(
                name="Women's Haircut",
                description="Professional haircut service for women, includes wash and style",
                duration_minutes=60,
                price=65.00,
                category="Hair"
            ),
            Service(
                name="Men's Haircut",
                description="Professional haircut service for men, includes wash and style",
                duration_minutes=45,
                price=45.00,
                category="Hair"
            ),
            Service(
                name="Hair Coloring",
                description="Full hair coloring service, includes toner and style",
                duration_minutes=120,
                price=120.00,
                category="Hair"
            ),
            Service(
                name="Manicure",
                description="Classic manicure with nail shaping, cuticle care, and polish",
                duration_minutes=45,
                price=35.00,
                category="Nails"
            ),
            Service(
                name="Pedicure",
                description="Classic pedicure with foot soak, scrub, and polish",
                duration_minutes=60,
                price=45.00,
                category="Nails"
            ),
            Service(
                name="Facial",
                description="Deep cleansing facial with massage and mask",
                duration_minutes=60,
                price=80.00,
                category="Skin"
            ),
            Service(
                name="Massage",
                description="Full body relaxation massage",
                duration_minutes=60,
                price=90.00,
                category="Body"
            ),
            Service(
                name="Highlights",
                description="Partial or full highlights with toner and style",
                duration_minutes=120,
                price=140.00,
                category="Hair"
            ),
        ]
        db.add_all(services)
        db.commit()

        # Create branches
        branches = [
            Branch(
                name="Downtown Salon",
                address="123 Main St",
                city="San Francisco",
                state="CA",
                phone="(415) 555-0123"
            ),
            Branch(
                name="Marina District",
                address="456 Beach Ave",
                city="San Francisco",
                state="CA",
                phone="(415) 555-0456"
            ),
        ]
        db.add_all(branches)
        db.commit()

        # Create staff members
        staff_members = []
        for branch in branches:
            staff_members.extend([
                Staff(
                    name=f"Staff {i+1} at {branch.name}",
                    email=f"staff{i+1}_{branch.id}@salon.com",
                    phone=f"(415) 555-{1000+i}",
                    role="Stylist",
                    branch_id=branch.id,
                    specialties="Hair,Color"
                )
                for i in range(5)  # 5 staff members per branch
            ])
        db.add_all(staff_members)
        db.commit()

        # Create customers
        customers = [
            Customer(
                name=f"Customer {i}",
                email=f"customer{i}@example.com",
                phone=f"(415) 555-{2000+i}",
                preferences="No chemical treatments"
            )
            for i in range(20)  # 20 customers
        ]
        db.add_all(customers)
        db.commit()

        # Create appointments
        appointments = []
        start_date = datetime.now() - timedelta(days=30)  # Start from 30 days ago
        
        for _ in range(164):  # Create 164 appointments
            customer = random.choice(customers)
            branch = random.choice(branches)
            staff = random.choice([s for s in staff_members if s.branch_id == branch.id])
            service = random.choice(services)
            
            # Random date within 60 days (30 days in past, 30 days in future)
            appointment_date = start_date + timedelta(
                days=random.randint(0, 60),
                hours=random.randint(9, 16),  # Between 9 AM and 4 PM
                minutes=random.choice([0, 30])  # On the hour or half hour
            )
            
            # Set status based on appointment date
            if appointment_date < datetime.now():
                status = random.choice([AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED])
            else:
                status = random.choice([AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED])
            
            appointments.append(
                Appointment(
                    customer_id=customer.id,
                    staff_id=staff.id,
                    branch_id=branch.id,
                    service_id=service.id,
                    appointment_time=appointment_date,
                    end_time=appointment_date + timedelta(minutes=service.duration_minutes),
                    status=status,
                    notes="Test appointment"
                )
            )
        
        db.add_all(appointments)
        db.commit()
        
        print("Test data created successfully!")
        
    except Exception as e:
        print(f"Error creating test data: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_data() 