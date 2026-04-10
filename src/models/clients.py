from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from src.db.db import Base

class Client(Base):
    __tablename__ = "cars"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    brand: Mapped[str] = mapped_column(String, index=True, nullable=False)
    model: Mapped[str] = mapped_column(String, index=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
