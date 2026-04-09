from abc import ABC, abstractmethod
from src.db import db

class AbstractRepository(ABC):
    @abstractmethod
    async def add_one(self, data):
        raise NotImplementedError

    @abstractmethod
    async def get_all(self):
        raise NotImplementedError

    @abstractmethod
    async def get_one(self, obj_id: int):
        raise NotImplementedError

    @abstractmethod
    async def update_one(self, obj_id: int, updated_data: dict):
        raise NotImplementedError

    @abstractmethod
    async def delete_one(self, obj_id: int):
        raise NotImplementedError