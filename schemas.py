from pydantic import BaseModel


class ItemBase(BaseModel):
    name: str
    description: str


class ItemCreate(ItemBase):
    pass


class ItemRead(ItemBase):
    id: int

    class Config:
        orm_mode = True  # Allows SQLAlchemy model instances to be returned
