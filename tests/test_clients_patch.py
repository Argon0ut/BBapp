from httpx import AsyncClient, ASGITransport
from src.main import app

async def create_client(ac):
    response = await ac.post(
        '/clients/create',
        json = {
            'brand': 'Ford',
            'model': 'Mustang',
            'year': 1964
        }
    )
    return response.json()

async def test_patch_client_partial_update():
    async with AsyncClient(
        transport = ASGITransport(app = app),
        base_url = 'http://testserver',
    ) as ac:
        client = await create_client(ac)
        client_id = client['id']

        response = await ac.patch(
            f'/clients/{client_id}',
            json = {
                'brand': 'Honda'
            }
        )
    assert response.status_code == 200
    data = response.json()

    assert data['brand'] == 'Honda'
    assert data['model'] == 'Mustang'
    assert data['year'] == 1964
