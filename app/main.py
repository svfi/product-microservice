import asyncio
import secrets
from typing import Annotated
from uuid import UUID

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, status, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from loguru import logger
from sqlalchemy import URL
from sqlmodel import create_engine, Session, SQLModel

from .config import Settings
from .product import db
from .product.error import ProductNotFoundError
from .product.model import ProductCreate, ProductPublic, ProductUpdate
from .offer.model import OfferPublic
from .offer.service.util import register_product, update_all_products_offers


settings = Settings()
database_url = URL.create(settings.database_driver,
                          settings.database_user,
                          settings.database_password,
                          settings.database_host,
                          settings.database_port,
                          settings.database_name)

engine = create_engine(database_url)


async def periodically_fetch_offers():
    while True:
        try:
            with Session(engine) as session:
                update_all_products_offers(settings.offers_service_refresh_token,
                                           settings.offers_service_base_url, session)
        except Exception as e:
            logger.error(f'An error occurred while fetching offers: {e}')
        await asyncio.sleep(settings.offers_service_fetch_period_seconds)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]

security = HTTPBasic()
CredentialsDep = Annotated[HTTPBasicCredentials, Depends(security)]


def get_current_username(credentials: CredentialsDep):
    current_username_bytes = credentials.username.encode("utf8")
    current_password_bytes = credentials.password.encode("utf8")

    are_credentials_same = secrets.compare_digest(current_username_bytes, current_password_bytes)

    if are_credentials_same:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect username or password",
                            headers={"WWW-Authenticate": "Basic"})

    return credentials.username


UserDep = Annotated[str, Depends(get_current_username)]

app = FastAPI()


@app.on_event('startup')
async def on_startup():
    SQLModel.metadata.create_all(engine)
    asyncio.create_task(periodically_fetch_offers())


@app.exception_handler(ProductNotFoundError)
async def product_not_found_error_handler(_: Request, exc: ProductNotFoundError):
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@app.post('/products/', response_model=ProductPublic, status_code=status.HTTP_202_ACCEPTED)
def create_product(product: ProductCreate, session: SessionDep, _: UserDep, background_tasks: BackgroundTasks):
    db_product = db.create_product(product, session)
    product_public = ProductPublic(**db_product.model_dump())
    background_tasks.add_task(register_product, product_public, settings.offers_service_refresh_token,
                              settings.offers_service_base_url, session)
    return db_product


@app.get('/products/{product_id}', response_model=ProductPublic, status_code=status.HTTP_200_OK)
def read_product(product_id: UUID, session: SessionDep):
    return db.read_product(product_id, session)


@app.put('/products/{product_id}', response_model=ProductPublic, status_code=status.HTTP_200_OK)
def update_product(product_id: UUID, product: ProductUpdate, session: SessionDep, _: UserDep):
    return db.update_product(product_id, product, session)


@app.delete('/products/{product_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: UUID, session: SessionDep, _: UserDep):
    db.delete_product(product_id, session)


@app.get('/products/{product_id}/offers', response_model=list[OfferPublic], status_code=status.HTTP_200_OK)
def read_product_offers(product_id: UUID, session: SessionDep):
    db_product = db.read_product(product_id, session)
    return db_product.offers
