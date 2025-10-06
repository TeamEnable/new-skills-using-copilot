# Notes

## Comparison with Django

Learn the patterns and idioms for transitioning to FastAPI from Django. 

### 1. Schemas: Pydantic vs Django Models/Forms

* Django: Uses Model classes for ORM and Form/Serializer classes for validation.
* FastAPI: Uses Pydantic models for request/response validation and serialization.

#### Example: User schema

**Django**

```
# models.py
from django.db import models

class User(models.Model):
    username = models.CharField(max_length=150)
    email = models.EmailField()

# forms.py
from django import forms

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']
```

**FastAPI**

```
# user_schama.py
from pydantic import BaseModel, EmailStr

class UserSchema(BaseModel):
    username: str
    email: EmailStr
```

#### Why?

Pydantic models are used to define the shape, types, and validation of data for requests and responses.
Separation of concerns: ORM (e.g., SQLAlchemy) models for DB, Pydantic models for data validation and transfer.

### 2. Dependency Injection

* Django: Relies heavily on global state (request object, settings, etc.)
* FastAPI: Uses explicit dependency injection via the Depends function.

#### Example: Auth Dependency

**Django**

```
from django.contrib.auth.decorators import login_required

@login_required
def profile(request):
    # request.user is available
    ...
```

**FastAPI**

```
from fastapi import Depends, HTTPException, status

def get_current_user(token: str = Depends(oauth2_scheme)):
    user = decode_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return user

# Usage in route
from fastapi import APIRouter

router = APIRouter()

@router.get("/profile")
def profile(current_user=Depends(get_current_user)):
    return {"username": current_user.username}
```

#### Why?

* Explicit dependencies make testing and code reuse easier.
* Composable: You can chain dependencies, reuse them, and override them in tests.

### 3. Database: SQLAlchemy (or SQLObject)

* Django: Built-in ORM; tightly coupled to models.
* FastAPI: No built-in ORM; commonly uses SQLAlchemy (or alternatives like SQLObject).

#### Example: SQLAlchemy Model & Usage

**Django**

```
# models.py
class Article(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
```

**FastAPI**

*Models using SQLAlchemy*

```
# models.py
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Article(Base):
    __tablename__ = "articles"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), index=True)
    content = Column(Text)
```

*Database Session Dependency*

```
# db.py
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

*Usage in Endpoint*

```
# main.py
from fastapi import Depends, FastAPI
from db import get_db
from models import Article
from sqlalchemy.orm import Session

app = FastAPI()

@app.post("/articles/")
def create_article(article: ArticleSchema, db: Session = Depends(get_db)):
    db_article = Article(**article.dict())
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    return db_article
```

#### Why?

* Explicit session management avoids hidden state.
* Separation of schema (Pydantic) from DB models (SQLAlchemy).

## More Details

* Testing: FastAPI’s dependency injection makes it easy to override dependencies in tests.
* Async Support: FastAPI natively supports async endpoints.
* Type Hints: FastAPI leverages Python type hints for validation and docs.

## Building a CRUD (Create, Read, Update, Delete) API

### 1. Database Model (SQLAlchemy)

Defines your data structure and how it maps to the database.

```
# models.py
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, index=True)
```

### 2. Pydantic Schemas

Used for data validation and serialization (requests and responses).

```
# schemas.py
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
```

### 3. Database Session Dependency

Manages database connections for each request.

```
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 4. CRUD Operations

Functions to interact with the database.

```
# crud.py
from models import Item
from schemas import ItemCreate
from sqlalchemy.orm import Session

def create_item(db: Session, item: ItemCreate):
    db_item = Item(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def get_items(db: Session, skip: int = 0, limit: int = 10):
    return db.query(Item).offset(skip).limit(limit).all()

def get_item(db: Session, item_id: int):
    return db.query(Item).filter(Item.id == item_id).first()

def update_item(db: Session, item_id: int, item: ItemCreate):
    db_item = get_item(db, item_id)
    if db_item:
        db_item.name = item.name
        db_item.description = item.description
        db.commit()
        db.refresh(db_item)
    return db_item

def delete_item(db: Session, item_id: int):
    db_item = get_item(db, item_id)
    if db_item:
        db.delete(db_item)
        db.commit()
    return db_item
```

### 5. FastAPI Endpoints

Defines the API routes and connects everything.

```
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
```

### Summary of What’s Needed

* **SQLAlchemy Models**: Define your database tables.
* **Pydantic Schemas**: Validate and serialize data.
* **DB Session Dependency**: Provide a database session per request.
* **CRUD Functions**: Implement logic for create, read, update, delete.
* **FastAPI Endpoints**: Wire everything together and handle HTTP requests.
