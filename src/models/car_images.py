from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from src.db.db import Base

from enum import Enum

class CarImageType(str, Enum):
    FRONT = 'front'
    REAR = 'rear'
    LEFT = 'left'
    RIGHT = 'right'


class CarImage(Base): #domain model for now
    __tablename__ = 'car_images'

    id : Mapped[int] = mapped_column(Integer, primarry_key=True, index=True)
    car_id : Mapped[int] = mapped_column(Integer, index=True)
    image_type : Mapped[CarImageType] = mapped_column(String, index=True)
    file_path : Mapped[str] = mapped_column(String, index=True)

