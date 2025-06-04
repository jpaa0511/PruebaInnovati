from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.schemas.book import Book, BookCreate, BookUpdate
from app.services.book_service import BookService

router = APIRouter()

@router.post("/", response_model=Book)
async def create_book(book: BookCreate, db: Session = Depends(get_db)):
    book_service = BookService(db)
    return await book_service.create_book(book)

@router.get("/", response_model=List[Book])
async def get_books(db: Session = Depends(get_db)):
    book_service = BookService(db)
    return await book_service.get_all_books()

@router.get("/{book_id}", response_model=Book)
async def get_book(book_id: int, db: Session = Depends(get_db)):
    book_service = BookService(db)
    book = await book_service.get_book(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    return book

@router.put("/{book_id}", response_model=Book)
async def update_book(book_id: int, book: BookUpdate, db: Session = Depends(get_db)):
    book_service = BookService(db)
    updated_book = await book_service.update_book(book_id, book)
    if not updated_book:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    return updated_book

@router.delete("/{book_id}")
async def delete_book(book_id: int, db: Session = Depends(get_db)):
    book_service = BookService(db)
    success = await book_service.delete_book(book_id)
    if not success:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    return {"message": "Libro eliminado exitosamente"}
