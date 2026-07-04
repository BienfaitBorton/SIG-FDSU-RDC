import os


DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/sig_fdsu_rdc",
)

DATA_MODE = os.environ.get("DATA_MODE", "json").strip().lower()

