from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel

from ..product.model import Product


class OfferBase(SQLModel):
    id: UUID = Field(primary_key=True)
    price: int
    items_in_stock: int


class Offer(OfferBase, table=True):
    product_id: UUID = Field(foreign_key='product.id')
    product: Product = Relationship(back_populates='offers')


class OfferPublic(OfferBase):
    pass
