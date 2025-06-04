from fastapi import APIRouter
from app.api.api_v1.endpoints import books, reservations, email

api_router = APIRouter()
 
api_router.include_router(books.router, prefix="/books", tags=["books"])

api_router.include_router(reservations.router, prefix="/reservations", tags=["reservations"])

api_router.include_router(email.router, prefix="/email", tags=["email"]) 