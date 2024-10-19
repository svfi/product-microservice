from uuid import UUID

from sqlmodel import Session

from .error import ProductNotFoundError
from .model import Product, ProductCreate, ProductUpdate
from ..offer.model import Offer, OfferPublic


def create_product(product: ProductCreate, session: Session) -> Product:
    db_product = Product.model_validate(product)
    session.add(db_product)
    session.commit()
    session.refresh(db_product)

    return db_product


def read_product(product_id: UUID, session: Session) -> Product:
    db_product = session.get(Product, product_id)

    if not db_product:
        raise ProductNotFoundError(f'Product with ID {product_id} does not exist')

    return db_product


def update_product(product_id: UUID, product: ProductUpdate, session: Session) -> Product:
    db_product = session.get(Product, product_id)

    if not db_product:
        raise ProductNotFoundError(f'Product with ID {product_id} does not exist')

    product_data = product.model_dump(exclude_unset=True)
    db_product.sqlmodel_update(product_data)
    session.add(db_product)
    session.commit()
    session.refresh(db_product)

    return db_product


def update_product_offers(product_id: UUID, offers: list[OfferPublic], session: Session) -> Product:
    db_product = session.get(Product, product_id)

    if not db_product:
        raise ProductNotFoundError(f'Product with ID {product_id} does not exist')

    db_offers = [Offer(**offer.model_dump(), product_id=product_id) for offer in offers]

    db_product.offers = db_offers
    session.add(db_product)
    session.commit()
    session.refresh(db_product)

    return db_product


def delete_product(product_id: UUID, session: Session):
    product = session.get(Product, product_id)

    if product:
        session.delete(product)
        session.commit()
