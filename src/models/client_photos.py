from sqlalchemy import Column, Integer, String
from src.db.db import Base

from enum import Enum

class ClientPhotoType(str, Enum):
    FRONT = 'front'
    REAR = 'rear'
    LEFT = 'left'
    RIGHT = 'right'


class ClientPhoto(Base):
    __tablename__ = 'car_images'

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, index=True)
    photo_type = Column(String, index=True)
    file_path = Column(String, index=True)
