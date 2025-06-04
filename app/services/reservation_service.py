from sqlalchemy.orm import Session
from app.models.reservation import Reservation
from app.models.book import Book
from app.schemas.reservation import ReservationCreate, ReservationUpdate
from typing import List, Optional
from datetime import datetime

class ReservationService:

    def __init__(self, db: Session):
        self.db = db

    async def create_reservation(self, book_id: int, user_email: str, end_date: datetime) -> Reservation:
        db_reservation = Reservation(
            book_id=book_id,
            user_email=user_email,
            end_date=end_date,
            is_active=True
        )
        self.db.add(db_reservation)
        
        book = self.db.query(Book).filter(Book.id == book_id).first()
        if book:
            book.available = False
        
        self.db.commit()
        self.db.refresh(db_reservation)
        return db_reservation

    async def get_reservation(self, reservation_id: int) -> Optional[Reservation]:
        return self.db.query(Reservation).filter(Reservation.id == reservation_id).first()

    async def get_active_reservation_by_email_and_book(self, user_email: str, book_title: str) -> Optional[Reservation]:
        return self.db.query(Reservation).join(Book).filter(
            Reservation.user_email == user_email,
            Book.title == book_title,
            Reservation.is_active == True
        ).first()

    async def get_user_reservations(self, user_email: str) -> List[Reservation]:
        return self.db.query(Reservation).filter(
            Reservation.user_email == user_email,
            Reservation.is_active == True
        ).all()

    async def renew_reservation(self, reservation_id: int, new_end_date: datetime) -> Optional[Reservation]:

        db_reservation = await self.get_reservation(reservation_id)
        if not db_reservation:
            return None

        db_reservation.end_date = new_end_date
        db_reservation.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(db_reservation)
        return db_reservation

    async def delete_reservation(self, user_email: str, book_title: str) -> bool:

        db_reservation = await self.get_active_reservation_by_email_and_book(user_email, book_title)
        if not db_reservation:
            return False

        db_reservation.is_active = False
        db_reservation.updated_at = datetime.utcnow()
        
        book = self.db.query(Book).filter(Book.id == db_reservation.book_id).first()
        if book:
            book.available = True
        
        self.db.commit()
        return True

    async def check_expired_reservations(self):

        current_time = datetime.utcnow()
        expired_reservations = self.db.query(Reservation).filter(
            Reservation.end_date < current_time,
            Reservation.is_active == True
        ).all()

        for reservation in expired_reservations:
            reservation.is_active = False
            book = self.db.query(Book).filter(Book.id == reservation.book_id).first()
            if book:
                book.available = True

        self.db.commit()
        return expired_reservations 