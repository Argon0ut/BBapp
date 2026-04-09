import pytest
import logging
from httpx import AsyncClient, ASGITransport

from src.main import app


#Test Isolation --> Runs before every test, No shared state bugs, Zero effort per test --> This pattern survives DB migrations
@pytest.fixture(autouse = True)
def clean_db():
    from src.db import db
    db.Cars.clear()


#ASGI-level integration tests
@pytest.mark.asyncio
async def test_create_cars():
    async with AsyncClient(
        transport = ASGITransport(app),
        base_url = 'http://testserver',
    ) as ac:
        response = await ac.post(
            '/cars/create',
            json = {
                "brand": "Toyota",
                "model": "GR86",
                "year": 2022
        })
    assert response.status_code == 201
    data = response.json()

    assert data["brand"] == "Toyota"
    assert data["model"] == "GR86"
    assert data["year"] == 2022
    assert 'id' in data

@pytest.mark.asyncio
async def test_patch_car_updates_only_given_fields():
    async with AsyncClient(
        transport = ASGITransport(app),
        base_url = 'http://testserver',
    ) as ac:
        create = await ac.post(
            '/cars/create',
            json={
                "brand": "Toyota",
                "model": "GR86",
                "year": 2022
            })
        car_id = create.json()['id']

        patch = await ac.patch(
            f'/cars/{car_id}',
            json={'brand' : 'Dodge'}
        )

    assert patch.status_code == 200
    data = patch.json()

    assert data["brand"] == "Dodge"
    assert data["model"] == "GR86"
    assert data["year"] == 2022

#Contract(Schema) test
async def test_create_car_response_contract():
    async with AsyncClient(
        transport = ASGITransport(app),
        base_url = 'http://testserver',
    ) as ac:
        response = await ac.post('/cars/create', json={
            "brand": "Toyota",
            "model": "GT86",
            "year": 2021
        })
    data= response.json()
    assert set(data.keys()) == {"id", "brand", "model", "year"}
    logging.info('created successfully!!!!!!!!!!!!!!')
