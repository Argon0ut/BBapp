from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from src.db.db import Base

from typing import List
from enum import Enum

# Key Note --> To denote some status choice kind of things, it is easy to use the Enum classes

class TuningStatus(Enum):
    PENDING = 'pending'
    COMPLETED = 'complete'
    FAILED = 'failed'



class TuningRequest(Base):
    id : Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    car_id : Mapped[int] = mapped_column(Integer, index=True)
    text_prompt : Mapped[str] = mapped_column(String, index=True)
    result_images : Mapped[List[str]] = mapped_column(String, index=True)
