# Notes

Learn the patterns and idioms for transitioning to FastAPI from Django. 

## 1. Schemas: Pydantic vs Django Models/Forms

* Django: Uses Model classes for ORM and Form/Serializer classes for validation.
* FastAPI: Uses Pydantic models for request/response validation and serialization.

### Example: User schema

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

### Why?

Pydantic models are used to define the shape, types, and validation of data for requests and responses.
Separation of concerns: ORM (e.g., SQLAlchemy) models for DB, Pydantic models for data validation and transfer.

## 2. Dependency Injection

* Django: Relies heavily on global state (request object, settings, etc.)
* FastAPI: Uses explicit dependency injection via the Depends function.

### Example: Auth Dependency

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

### Why?

* Explicit dependencies make testing and code reuse easier.
* Composable: You can chain dependencies, reuse them, and override them in tests.

## 3. Database: SQLAlchemy (or SQLObject)

* Django: Built-in ORM; tightly coupled to models.
* FastAPI: No built-in ORM; commonly uses SQLAlchemy (or alternatives like SQLObject).

### Example: SQLAlchemy Model & Usage

**Django**

```
# models.py
class Article(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
```

**FastAPI**

**Models using SQLAlchemy**

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

**Database Session Dependency**

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

**Usage in Endpoint**

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

### Why?

* Explicit session management avoids hidden state.
* Separation of schema (Pydantic) from DB models (SQLAlchemy).

