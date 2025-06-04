from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.email_processor import EmailProcessor
from app.services.graph_api import GraphAPIService
from app.schemas.email import EmailProcessRequest, EmailResponse
from typing import List, Dict, Any
from datetime import datetime

router = APIRouter()
graph_api = GraphAPIService()

@router.post("/process", response_model=EmailResponse)
async def process_email(
    request: EmailProcessRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    processor = EmailProcessor(db)
    result = await processor.process_email(request.email_content, request.user_email)
    return result

@router.post("/check", response_model=EmailResponse)
async def check_new_emails(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    processor = EmailProcessor(db)
    result = await processor.process_unread_emails()
    return {
        "message": f"Procesados {result['processed_count']} correos",
        "result": result
    }

@router.post("/check-expired")
async def check_expired_reservations(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    from app.services.reservation_service import ReservationService
    
    reservation_service = ReservationService(db)
    expired_reservations = await reservation_service.check_expired_reservations()
    
    graph_api = GraphAPIService()
    for reservation in expired_reservations:
        background_tasks.add_task(
            graph_api.send_email,
            to=reservation.user_email,
            subject="Tu reserva ha expirado",
            body=f"Tu reserva del libro '{reservation.book.title}' ha expirado. Por favor, devuelve el libro lo antes posible."
        )
    
    return {"message": f"Verificadas {len(expired_reservations)} reservas expiradas"}

@router.get("/test-connection")
async def test_email_connection():
    try:
        graph_api = GraphAPIService()
        emails = await graph_api.get_unread_emails()
        return {
            "status": "success",
            "message": "Conexión exitosa con Microsoft Graph API",
            "emails_found": len(emails),
            "emails": emails
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error al conectar con Microsoft Graph API: {str(e)}"
        } 