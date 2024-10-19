from sqlmodel import Field, SQLModel


class AccessToken(SQLModel, table=True):
    id: int = Field(default=1, primary_key=True)
    value: str
