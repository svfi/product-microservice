import pytest
from sqlmodel import create_engine, Session, SQLModel

from ..offer.service.db import read_token, update_token
from ..offer.service.model import AccessToken


TOKEN1 = AccessToken(value='abc')
TOKEN2 = AccessToken(value='def')

DATABASE_URL = 'sqlite:///test.db'
CONNECT_ARGS = {'check_same_thread': False}
engine = create_engine(DATABASE_URL, connect_args=CONNECT_ARGS)


@pytest.fixture(scope='function', autouse=True)
def empty_database():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


@pytest.fixture(scope='function')
def session():
    with Session(engine) as session:
        yield session


def test_read_token(session):
    token = read_token(session)
    assert token is None


def test_create_token(session):
    update_token(TOKEN1, session)
    token = read_token(session)
    assert token == TOKEN1


def test_update_token(session):
    update_token(TOKEN1, session)
    update_token(TOKEN2, session)
    token = read_token(session)
    assert token == TOKEN2
