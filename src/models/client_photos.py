from sqlalchemy import Column, ForeignKey, Integer, String
from src.db.db import Base

from enum import Enum

class ClientPhotoType(str, Enum):
    FRONT = 'front'
    REAR = 'rear'
    LEFT = 'left'
    RIGHT = 'right'


class ClientPhoto(Base):
    __tablename__ = 'client_photos'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("auth_users.id", ondelete="CASCADE"), index=True, nullable=False)
    photo_type = Column(String, index=True)
    file_path = Column(String, index=True)
