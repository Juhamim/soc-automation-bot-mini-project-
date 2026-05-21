import sys
import os
from sqlalchemy.orm import Session

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.session import SessionLocal
from app.database.crud import create_user, get_user_by_username
from app.core.security import get_password_hash
from app.database.models import Base
from app.database.session import engine

def pre_create_tables():
    print("Ensuring users table exists...")
    Base.metadata.create_all(bind=engine)

def seed_admin_user():
    db: Session = SessionLocal()
    try:
        # Check if admin already exists
        admin_user = get_user_by_username(db, "admin")
        if admin_user:
            print("Admin user already exists. Skipping.")
            return

        print("Creating default admin user...")
        
        # In a real app, use environment variables for raw passwords
        # This is strictly a local dev default for the SOC Automated Bot
        password_hash = get_password_hash("password123")
        
        create_user(
            db=db,
            username="admin",
            email="admin@socbot.local",
            password_hash=password_hash,
            role="Admin"
        )
        print("Admin user created successfully!")
        print("Username: admin")
        print("Password: password123")
        
    except Exception as e:
        print(f"Error seeding user: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    pre_create_tables()
    seed_admin_user()
