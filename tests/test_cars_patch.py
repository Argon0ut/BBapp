from httpx import AsyncClient, ASGITransport
from src.main import app

async def create_car(ac):
    response = await ac.post(
        '/cars/create',
        json = {
            'brand': 'Ford',
            'model': 'Mustang',
            'year': 1964
        }
    )
    return response.json()

async def test_patch_car_partial_update():
    async with AsyncClient(
        transport = ASGITransport(app = app),
        base_url = 'http://testserver',
    ) as ac:
        car = await create_car(ac)
        car_id = car['id']

        response = await ac.patch(
            f'/cars/{car_id}',
            json = {
                'brand': 'Honda'
            }
        )
    assert response.status_code == 200
    data = response.json()

    assert data['brand'] == 'Honda'
    assert data['model'] == 'Mustang'
    assert data['year'] == 1964