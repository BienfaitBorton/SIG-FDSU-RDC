from sqlalchemy import create_engine, inspect
from app.config import DATABASE_URL

# Create the SQLAlchemy engine. Do NOT call `Base.metadata.create_all`
# automatically at import time: table creation should be explicit (CLI or
# migrations) to avoid accidental schema changes during imports or runtime.
engine = create_engine(DATABASE_URL)

from app.models import Base


def create_all_tables() -> None:
	"""Create all tables from SQLAlchemy models.

	This function is intended to be used only during project initialization
	(or by a controlled bootstrap script). Prefer Alembic migrations for
	schema evolution in production.
	"""
	Base.metadata.create_all(engine)


def tables_exist(table_names: list[str]) -> dict[str, bool]:
	"""Return a mapping table_name -> bool indicating whether each table exists."""
	inspector = inspect(engine)
	return {t: inspector.has_table(t) for t in table_names}