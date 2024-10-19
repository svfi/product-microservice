from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel


class ProductBase(SQLModel):
    name: str
    description: str


class Product(ProductBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    offers: list['Offer'] = Relationship(back_populates='product', cascade_delete=True)


class ProductPublic(ProductBase):
    id: UUID


class ProductCreate(ProductBase):
    pass


class ProductUpdate(ProductBase):
    pass
