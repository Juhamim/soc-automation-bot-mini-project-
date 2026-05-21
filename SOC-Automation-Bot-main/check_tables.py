import sqlalchemy
from app.database.session import engine
from app.database.models import Base

print("Tables in Base:", Base.metadata.tables.keys())

inspector = sqlalchemy.inspect(engine)
print("Tables in DB:", inspector.get_table_names())
