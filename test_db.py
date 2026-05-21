import json

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, inspect
from app.core.config import settings

try:
    engine = create_engine(settings.DATABASE_URL)
    inspector = inspect(engine)
    columns = inspector.get_columns('threat_indicators')
    with open('error.json', 'w') as f:
        json.dump({"columns": [c['name'] for c in columns]}, f, indent=2)
except Exception as e:
    with open('error.json', 'w') as f:
        json.dump({"error": str(e)}, f, indent=2)
