from uuid import UUID

from fastapi import status
from fastapi.testclient import TestClient
import pytest
from sqlmodel import create_engine, Session, SQLModel

from ..main import app, get_session
from ..offer.model import OfferPublic
from ..product.db import update_product_offers


PRODUCTS_PATH = '/products'

PRODUCT_NAME1 = 'product1'
PRODUCT_DESCRIPTION1 = 'something'
PRODUCT_CREATE_DATA1 = {'name': PRODUCT_NAME1, 'description': PRODUCT_DESCRIPTION1}

PRODUCT_NAME2 = 'product2'
PRODUCT_DESCRIPTION2 = 'else'
PRODUCT_CREATE_DATA2 = {'name': PRODUCT_NAME2, 'description': PRODUCT_DESCRIPTION2}

PRODUCT_CREATE_INVALID_DATA = {'name': None, 'description': 574}

SOME_RANDOM_UUID = 'e966cb0e-4f81-43d2-a026-d919ae7f5d89'

OFFER1 = OfferPublic(id=UUID('8becdfb2-0c84-4ccb-8c9f-e1f8f2d5cf6c'), price=500, items_in_stock=42)
OFFER2 = OfferPublic(id=UUID('e5997bef-a499-4335-ae94-95e10501b33b'), price=104, items_in_stock=5)

DATABASE_URL = 'sqlite:///test.db'
CONNECT_ARGS = {'check_same_thread': False}
engine = create_engine(DATABASE_URL, connect_args=CONNECT_ARGS)


@pytest.fixture(scope='function', autouse=True)
def empty_database():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def get_test_session():
    with Session(engine) as session:
        yield session


@pytest.fixture(scope='function')
def session():
    yield from get_test_session()


@pytest.fixture(scope='function', autouse=True)
def mock_background_tasks(mocker):
    mocker.patch('fastapi.BackgroundTasks.add_task')


app.dependency_overrides[get_session] = get_test_session

client = TestClient(app)


def test_create_product():
    response = client.post(PRODUCTS_PATH, json=PRODUCT_CREATE_DATA1)
    assert response.status_code == status.HTTP_202_ACCEPTED

    data = response.json()
    UUID(data['id'])
    assert data['name'] == PRODUCT_NAME1
    assert data['description'] == PRODUCT_DESCRIPTION1


def test_create_invalid_product():
    response = client.post(PRODUCTS_PATH, json=PRODUCT_CREATE_INVALID_DATA)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_read_product():
    response = client.post(PRODUCTS_PATH, json=PRODUCT_CREATE_DATA1)
    assert response.status_code == status.HTTP_202_ACCEPTED

    data = response.json()
    product_id = data['id']

    response = client.get(f'{PRODUCTS_PATH}/{product_id}')
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data['id'] == product_id
    assert data['name'] == PRODUCT_NAME1
    assert data['description'] == PRODUCT_DESCRIPTION1


def test_read_invalid_product():
    response = client.get(f'{PRODUCTS_PATH}/{SOME_RANDOM_UUID}')
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_product():
    response = client.post(PRODUCTS_PATH, json=PRODUCT_CREATE_DATA1)
    assert response.status_code == status.HTTP_202_ACCEPTED

    data = response.json()
    product_id = data['id']

    response = client.put(f'{PRODUCTS_PATH}/{product_id}', json=PRODUCT_CREATE_DATA2)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data['id'] == product_id
    assert data['name'] == PRODUCT_NAME2
    assert data['description'] == PRODUCT_DESCRIPTION2


def test_delete_product():
    response = client.post(PRODUCTS_PATH, json=PRODUCT_CREATE_DATA1)
    assert response.status_code == status.HTTP_202_ACCEPTED

    data = response.json()
    product_id = data['id']

    response = client.delete(f'{PRODUCTS_PATH}/{product_id}')
    assert response.status_code == status.HTTP_204_NO_CONTENT

    response = client.get(f'{PRODUCTS_PATH}/{product_id}')
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_invalid_product():
    response = client.get(f'{PRODUCTS_PATH}/{SOME_RANDOM_UUID}')
    assert response.status_code == status.HTTP_404_NOT_FOUND

    response = client.delete(f'{PRODUCTS_PATH}/{SOME_RANDOM_UUID}')
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_read_product_offers(session):
    response = client.post(PRODUCTS_PATH, json=PRODUCT_CREATE_DATA1)
    assert response.status_code == status.HTTP_202_ACCEPTED

    data = response.json()
    product_id = data['id']

    offers = [OFFER1, OFFER2]
    update_product_offers(UUID(product_id), offers, session)

    response = client.get(f'{PRODUCTS_PATH}/{product_id}/offers')
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert len(data) == 2
    for offer in offers:
        found_offer = next(item for item in data if item['id'] == str(offer.id))
        assert found_offer['price'] == offer.price
        assert found_offer['items_in_stock'] == offer.items_in_stock


def test_update_product_with_offers(session):
    """Test update of product with offers to see if the offers will be still linked to the product after the update."""
    response = client.post(PRODUCTS_PATH, json=PRODUCT_CREATE_DATA1)
    assert response.status_code == status.HTTP_202_ACCEPTED

    data = response.json()
    product_id = data['id']

    offers = [OFFER1, OFFER2]
    update_product_offers(UUID(product_id), offers, session)

    response = client.put(f'{PRODUCTS_PATH}/{product_id}', json=PRODUCT_CREATE_DATA2)
    assert response.status_code == status.HTTP_200_OK

    response = client.get(f'{PRODUCTS_PATH}/{product_id}/offers')
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert len(data) == 2
