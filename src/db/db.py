import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

DB_URL = os.getenv('DB_URL')


if not DB_URL:
    raise ValueError("DB_URL is not set")

# 1) Create engine
# 2) Session
# 3) Base -> used by models in models.py
# 4) get_db() returns session in 2

engine = create_async_engine(DB_URL, echo=False)
try:
    from sqlalchemy.ext.asyncio import async_sessionmaker
    AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)
except ImportError:
    AsyncSessionLocal = sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


try:
    from sqlalchemy.orm import DeclarativeBase

    class Base(DeclarativeBase):
        pass
except ImportError:
    from sqlalchemy.orm import declarative_base

    Base = declarative_base()

async def get_db_session():
    async with AsyncSessionLocal() as session:
        yield session
