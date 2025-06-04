import logging
from app.services.email_processor import EmailProcessor
from app.db.session import SessionLocal

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_emails():
    """Verifica y procesa los correos no leídos."""
    db = SessionLocal()
    try:
        processor = EmailProcessor(db)
        result = await processor.process_unread_emails()
        logger.info(f"Procesados {result.get('processed_count', 0)} correos")
        if result.get('errors'):
            logger.error("Errores encontrados:")
            for error in result['errors']:
                logger.error(f"- {error}")
    except Exception as e:
        logger.error(f"Error al verificar correos: {str(e)}")
    finally:
        db.close() 