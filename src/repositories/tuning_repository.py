from src.models.tuning_request import TuningRequest
from src.db import db
from src.utils.repository import PlainRepository


class TuningRepository(PlainRepository):

    async def add(self, car_id : int, request : TuningRequest):
        db.TuningRequests.append(request)
        return request

    async def get(self, request_id : int):
        result = None
        for request in db.TuningRequests:
            if request.id == request_id:
                result = request
                break
        return result

    async def update(self, request_id : int, request : TuningRequest):
        for elem in db.TuningRequests:
            if elem.id == request_id:
                elem = request
                return elem
        return None

    async def delete(self, request_id : int):
        for i in range(len(db.TuningRequests)):
            if db.TuningRequests[i].id == request_id:
                request = db.TuningRequests[i].pop(i)
                return request
        return None

    async def _next_id(self):
        if not db.TuningRequests:
            return 0
        else:
            return db.TuningRequests[-1].id + 1
