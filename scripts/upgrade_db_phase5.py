import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database.session import engine
from app.database.models import Base
from sqlalchemy import text

def upgrade():
    print("Creating new tables...")
    Base.metadata.create_all(bind=engine)
    
    print("Adding incident_id column to alerts table...")
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE alerts ADD COLUMN incident_id UUID REFERENCES incidents(id) ON DELETE SET NULL;"))
            conn.commit()
            print("Successfully added incident_id column to alerts.")
        except Exception as e:
            print(f"Column might already exist or another error occurred: {e}")

if __name__ == "__main__":
    upgrade()
