from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from src.db.db import Base

from enum import Enum

class ClientPhotoType(str, Enum):
    FRONT = 'front'
    REAR = 'rear'
    LEFT = 'left'
    RIGHT = 'right'


class ClientPhoto(Base):
    __tablename__ = 'car_images'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    client_id: Mapped[int] = mapped_column(Integer, index=True)
    photo_type: Mapped[ClientPhotoType] = mapped_column(String, index=True)
    file_path: Mapped[str] = mapped_column(String, index=True)
