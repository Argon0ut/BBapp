from sqlalchemy import Column, Integer, String
from src.db.db import Base

class Client(Base):
    __tablename__ = "cars"

    id = Column(Integer, primary_key=True, index=True)
    brand = Column(String, index=True, nullable=False)
    model = Column(String, index=True, nullable=False)
    year = Column(Integer, nullable=False)
