import logging
from sqlalchemy import create_engine
from app.core.config import settings
from app.database.models import Base

logging.basicConfig(filename='db_creation.log', filemode='w', level=logging.INFO)
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

try:
    engine = create_engine(settings.DATABASE_URL, echo=True)
    Base.metadata.create_all(bind=engine)
except Exception as e:
    logging.error(f'Creation Failed: {e}')

