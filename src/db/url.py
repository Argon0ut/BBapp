import os

from dotenv import load_dotenv


load_dotenv()


def get_database_url() -> str:
    raw_url = (os.getenv("DB_URL") or os.getenv("DATABASE_URL") or "").strip().strip("\"'")

    if not raw_url:
        raise ValueError("Database URL is not set. Configure DB_URL or DATABASE_URL.")

    if raw_url.startswith("postgres://"):
        return raw_url.replace("postgres://", "postgresql+asyncpg://", 1)

    if raw_url.startswith("postgresql://") and "+asyncpg" not in raw_url:
        return raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    return raw_url
