from sqlalchemy import create_engine
from app.config import DATABASE_URL

engine = create_engine(DATABASE_URL)
from app.models import Base

Base.metadata.create_all(engine)