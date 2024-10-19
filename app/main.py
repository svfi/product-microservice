from typing import Annotated
from uuid import UUID

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, status, Request
from sqlalchemy import URL
from sqlmodel import create_engine, Session, SQLModel

from .config import Settings
from .product import db
from .product.error import ProductNotFoundError
from .product.model import ProductCreate, ProductPublic, ProductUpdate
from .offer.model import OfferPublic
from .offer.service.util import register_product


settings = Settings()
database_url = URL.create(settings.database_driver,
                          settings.database_user,
                          settings.database_password,
                          settings.database_host,
                          settings.database_port,
                          settings.database_name)

engine = create_engine(database_url)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]

app = FastAPI()


@app.exception_handler(ProductNotFoundError)
async def product_not_found_error_handler(_: Request, exc: ProductNotFoundError):
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@app.on_event('startup')
def on_startup():
    SQLModel.metadata.create_all(engine)


@app.post('/products/', response_model=ProductPublic, status_code=status.HTTP_202_ACCEPTED)
def create_product(product: ProductCreate, session: SessionDep, background_tasks: BackgroundTasks):
    db_product = db.create_product(product, session)
    product_public = ProductPublic(**db_product.model_dump())
    background_tasks.add_task(register_product, product_public, settings.offers_service_refresh_token,
                              settings.offers_service_base_url, session)
    return db_product


@app.get('/products/{product_id}', response_model=ProductPublic, status_code=status.HTTP_200_OK)
def read_product(product_id: UUID, session: SessionDep):
    return db.read_product(product_id, session)


@app.put('/products/{product_id}', response_model=ProductPublic, status_code=status.HTTP_200_OK)
def update_product(product_id: UUID, product: ProductUpdate, session: SessionDep):
    return db.update_product(product_id, product, session)


@app.delete('/products/{product_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: UUID, session: SessionDep):
    db.delete_product(product_id, session)


@app.get('/products/{product_id}/offers', response_model=list[OfferPublic], status_code=status.HTTP_200_OK)
def read_product_offers(product_id: UUID, session: SessionDep):
    db_product = db.read_product(product_id, session)
    return db_product.offers
