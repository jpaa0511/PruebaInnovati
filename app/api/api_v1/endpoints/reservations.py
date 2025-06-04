from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
from app.db.session import get_db
from app.schemas.reservation import Reservation, ReservationCreate, ReservationUpdate
from app.services.reservation_service import ReservationService

router = APIRouter()

@router.post("/", response_model=Reservation)
async def create_reservation(reservation: ReservationCreate, db: Session = Depends(get_db)):
    reservation_service = ReservationService(db)
    return await reservation_service.create_reservation(
        book_id=reservation.book_id,
        user_email=reservation.user_email,
        end_date=reservation.end_date
    )

@router.get("/user/{user_email}", response_model=List[Reservation])
async def get_user_reservations(user_email: str, db: Session = Depends(get_db)):
    reservation_service = ReservationService(db)
    return await reservation_service.get_user_reservations(user_email)

@router.get("/{reservation_id}", response_model=Reservation)
async def get_reservation(reservation_id: int, db: Session = Depends(get_db)):
    reservation_service = ReservationService(db)
    reservation = await reservation_service.get_reservation(reservation_id)
    if not reservation:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    return reservation

@router.put("/{reservation_id}/renew", response_model=Reservation)
async def renew_reservation(reservation_id: int, db: Session = Depends(get_db)):
    reservation_service = ReservationService(db)
    new_end_date = datetime.utcnow() + timedelta(days=14)
    updated_reservation = await reservation_service.renew_reservation(reservation_id, new_end_date)
    if not updated_reservation:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    return updated_reservation

@router.delete("/{reservation_id}")
async def delete_reservation(reservation_id: int, db: Session = Depends(get_db)):

    reservation_service = ReservationService(db)
    reservation = await reservation_service.get_reservation(reservation_id)
    if not reservation:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    
    success = await reservation_service.delete_reservation(
        user_email=reservation.user_email,
        book_title=reservation.book.title
    )
    return {"message": "Reserva eliminada exitosamente"} 