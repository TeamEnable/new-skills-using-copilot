from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas import ItemCreate, ItemRead
from crud import create_item, get_items, get_item, update_item, delete_item

app = FastAPI()


@app.post("/items/", response_model=ItemRead)
def create(item: ItemCreate, db: Session = Depends(get_db)):
    return create_item(db, item)


@app.get("/items/", response_model=list[ItemRead])
def read_items(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return get_items(db, skip, limit)


@app.get("/items/{item_id}", response_model=ItemRead)
def read_item(item_id: int, db: Session = Depends(get_db)):
    db_item = get_item(db, item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item


@app.put("/items/{item_id}", response_model=ItemRead)
def update(item_id: int, item: ItemCreate, db: Session = Depends(get_db)):
    db_item = update_item(db, item_id, item)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item


@app.delete("/items/{item_id}", response_model=ItemRead)
def delete(item_id: int, db: Session = Depends(get_db)):
    db_item = delete_item(db, item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item


# Needed to init the database
from models import Base
from database import engine

# This creates all tables defined by SQLAlchemy models (if they don't exist)
Base.metadata.create_all(bind=engine)
