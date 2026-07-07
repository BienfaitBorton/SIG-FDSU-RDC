import os

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "sig_fdsu_rdc")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "test123")

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
)

DATA_MODE = os.environ.get("DATA_MODE", "json").strip().lower()


def connect_db(**kwargs):
    """Open a psycopg2 connection using the project DATABASE_URL."""
    import psycopg2

    try:
        return psycopg2.connect(DATABASE_URL, **kwargs)
    except UnicodeDecodeError as exc:
        # Sur Windows (locale fr), libpq peut renvoyer des messages d'erreur en CP1252
        # avant la négociation client_encoding ; psycopg2 les décode alors en UTF-8.
        raise psycopg2.OperationalError(
            "Connexion PostgreSQL impossible : vérifiez DATABASE_URL, DB_PASSWORD "
            "et l'existence de la base (message serveur encodé CP1252 masqué)."
        ) from exc
