from sqlalchemy.orm import Session
from app.models.book import Book
from app.schemas.book import BookCreate, BookUpdate
from typing import List, Optional
from datetime import datetime

class BookService:

    def __init__(self, db: Session):
        self.db = db

    async def create_book(self, book_data: BookCreate) -> Book:
        db_book = Book(**book_data.dict())
        self.db.add(db_book)
        self.db.commit()
        self.db.refresh(db_book)
        return db_book

    async def get_book(self, book_id: int) -> Optional[Book]:
        return self.db.query(Book).filter(Book.id == book_id).first()

    async def get_book_by_title(self, title: str) -> Optional[Book]:
        return self.db.query(Book).filter(Book.title == title).first()

    async def get_all_books(self) -> List[Book]:
        return self.db.query(Book).all()

    async def update_book(self, book_id: int, book_data: BookUpdate) -> Optional[Book]:

        db_book = await self.get_book(book_id)
        if not db_book:
            return None

        update_data = book_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_book, field, value)

        db_book.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(db_book)
        return db_book

    async def delete_book(self, book_id: int) -> bool:

        db_book = await self.get_book(book_id)
        if not db_book:
            return False

        self.db.delete(db_book)
        self.db.commit()
        return True

    async def delete_book_by_title(self, title: str) -> bool:

        db_book = await self.get_book_by_title(title)
        if not db_book:
            return False

        self.db.delete(db_book)
        self.db.commit()
        return True 