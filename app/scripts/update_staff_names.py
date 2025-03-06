import os
import sys

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db.session import SessionLocal
from app.models import Staff

# List of realistic stylist names
STYLIST_NAMES = [
    "Emma Thompson",
    "James Rodriguez",
    "Sophia Chen",
    "Michael Williams",
    "Isabella Martinez",
    "Daniel Kim",
    "Olivia Parker",
    "Alexander Davis",
    "Ava Johnson",
    "Lucas Garcia"
]

def update_staff_names():
    db = SessionLocal()
    try:
        staff_members = db.query(Staff).all()
        for i, staff in enumerate(staff_members):
            if i < len(STYLIST_NAMES):
                staff.name = STYLIST_NAMES[i]
                # Update email to match new name
                email = STYLIST_NAMES[i].lower().replace(" ", ".") + "@salon.com"
                staff.email = email
        db.commit()
        print("Staff names updated successfully!")
        
        # Print the updated names
        print("\nUpdated staff list:")
        for staff in staff_members:
            print(f"- {staff.name} ({staff.role}) at {staff.branch_id}")
    except Exception as e:
        print(f"Error updating staff names: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_staff_names() 