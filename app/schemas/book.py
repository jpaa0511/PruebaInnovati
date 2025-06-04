from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class BookBase(BaseModel):
    title: str
    author: str
    isbn: str
    publication_year: int
    available: bool = True

class BookCreate(BookBase):
    pass

class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    isbn: Optional[str] = None
    publication_year: Optional[int] = None
    available: Optional[bool] = None

class BookInDBBase(BookBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class Book(BookInDBBase):
    pass