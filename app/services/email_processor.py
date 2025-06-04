from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from openai import OpenAI
from app.services.graph_api import GraphAPIService
from app.services.book_service import BookService
from app.services.reservation_service import ReservationService
from app.db.session import SessionLocal
from app.core.config import settings
from app.schemas.book import BookCreate
from datetime import datetime, timedelta
import json
import logging
import re
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailProcessor:

    def __init__(self, db: Optional[Session] = None):
        self.db = db or SessionLocal()
        self.book_service = BookService(self.db)
        self.reservation_service = ReservationService(self.db)
        self.graph_api = GraphAPIService()
        
        try:
            self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
            test_response = self.openai_client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            logger.info("Conexión con OpenAI establecida correctamente")
        except Exception as e:
            logger.error(f"Error al conectar con OpenAI: {str(e)}")
            raise

    def _clean_html_content(self, html_content: str) -> str:

        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)
            text = re.sub(r'\s+', ' ', text)
            return text.strip()
        except Exception as e:
            logger.error(f"Error al limpiar HTML: {str(e)}")
            return html_content

    async def _analyze_email_content(self, content: str) -> Dict[str, Any]:

        try:
            system_prompt = """Eres un asistente de biblioteca. Analiza el correo y responde SOLO con un objeto JSON.
            El JSON debe tener esta estructura exacta:
            {
                "action": "RESERVAR|RENOVAR|ELIMINAR|LISTAR|CREAR|ELIMINAR_LIBRO",
                "book_title": "título del libro" (para RESERVAR/RENOVAR/ELIMINAR/CREAR/ELIMINAR_LIBRO),
                "book_author": "autor del libro" (solo para CREAR),
                "book_isbn": "isbn del libro" (solo para CREAR),
                "book_year": año de publicación (solo para CREAR)
            }
            
            Acciones disponibles:
            - RESERVAR: Para reservar un libro existente
            - RENOVAR: Para renovar una reserva existente
            - ELIMINAR: Para eliminar una reserva existente
            - ELIMINAR_LIBRO: Para eliminar un libro de la biblioteca
            - LISTAR: Para ver todos los libros
            - CREAR: Para crear un nuevo libro
            
            Si el correo menciona eliminar un libro de la biblioteca, usa la acción ELIMINAR_LIBRO.
            Si el correo menciona eliminar una reserva, usa la acción ELIMINAR.
            
            No incluyas ningún texto adicional, solo el JSON."""

            user_prompt = f"Analiza este correo y responde con el JSON: {content}"

            logger.info("=== PROMPT ENVIADO A OPENAI ===")
            logger.info(f"System: {system_prompt}")
            logger.info(f"User: {user_prompt}")
            logger.info("=============================")

            response = self.openai_client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0,
                max_tokens=150
            )

            result = response.choices[0].message.content.strip()
            
            logger.info("=== RESPUESTA DE OPENAI ===")
            logger.info(f"Respuesta cruda: {result}")
            logger.info("=========================")

            cleaned_result = result
            cleaned_result = re.sub(r'```json\s*', '', cleaned_result)
            cleaned_result = re.sub(r'```\s*', '', cleaned_result)
            cleaned_result = re.sub(r'[\n\r\t]', '', cleaned_result)
            cleaned_result = re.sub(r'\s+', ' ', cleaned_result)
            cleaned_result = cleaned_result.strip()
            
            logger.info(f"Respuesta limpia: {cleaned_result}")

            try:
                action_data = json.loads(cleaned_result)
                logger.info(f"JSON parseado exitosamente: {action_data}")
                
                if action_data["action"] == "ELIMINAR" and "eliminar el libro" in content.lower():
                    action_data["action"] = "ELIMINAR_LIBRO"
                    logger.info(f"Acción corregida a ELIMINAR_LIBRO basado en el contenido del correo")
                
                return action_data
            except json.JSONDecodeError as e:
                logger.error(f"Error al parsear JSON: {str(e)}")
                logger.error(f"Contenido que causó el error: {cleaned_result}")
                raise ValueError(f"La respuesta no es un JSON válido: {cleaned_result}")

        except Exception as e:
            logger.error(f"Error al analizar el correo: {str(e)}")
            logger.error(f"Tipo de error: {type(e)}")
            raise

    async def process_email(self, email_content: str, user_email: str) -> Dict[str, Any]:

        try:
            logger.info(f"Procesando correo de {user_email}")
            
            clean_content = self._clean_html_content(email_content)
            logger.info(f"Contenido limpio del correo: {clean_content}")

            action_data = await self._analyze_email_content(clean_content)
            
            response = await self._execute_action(action_data, user_email)
            logger.info(f"Respuesta de la acción: {response}")
            
            await self.graph_api.send_email(
                to=user_email,
                subject="Respuesta a tu solicitud de biblioteca",
                body=response
            )

            return {"status": "success", "message": response}
                
        except Exception as e:
            error_message = f"Error al procesar el correo: {str(e)}"
            logger.error(error_message)
            await self.graph_api.send_email(
                to=user_email,
                subject="Error en tu solicitud de biblioteca",
                body="Lo siento, no pude procesar tu solicitud correctamente. Por favor, intenta reformularla."
            )
            return {"status": "error", "message": error_message}

    async def process_unread_emails(self) -> Dict[str, Any]:

        try:
            logger.info("Buscando correos no leídos...")
            unread_emails = await self.graph_api.get_unread_emails()
            logger.info(f"Encontrados {len(unread_emails)} correos no leídos")
            
            processed_count = 0
            errors = []

            for email in unread_emails:
                try:
                    email_content = email["body"]["content"]
                    user_email = email["from"]["emailAddress"]["address"]
                    logger.info(f"Procesando correo de {user_email}")

                    await self.process_email(email_content, user_email)

                    await self.graph_api.mark_email_as_read(email["id"])
                    processed_count += 1
                    logger.info(f"Correo procesado exitosamente")
                except Exception as e:
                    error_msg = f"Error procesando correo {email['id']}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)

            return {
                "status": "success",
                "processed_count": processed_count,
                "errors": errors
            }
        except Exception as e:
            error_msg = f"Error al procesar correos: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "message": error_msg
            }

    async def _execute_action(self, action_data: Dict[str, Any], user_email: str) -> str:

        action = action_data.get("action")
        
        if action == "RESERVAR":
            book = await self.book_service.get_book_by_title(action_data["book_title"])
            if not book:
                return f"Lo siento, no se encontró el libro '{action_data['book_title']}'."
            if not book.available:
                return f"Lo siento, el libro '{book.title}' no está disponible en este momento."
            
            end_date = datetime.utcnow() + timedelta(days=15)
            
            reservation = await self.reservation_service.create_reservation(
                book_id=book.id,
                user_email=user_email,
                end_date=end_date
            )
            return f"Has reservado exitosamente el libro '{book.title}' hasta el {end_date.strftime('%d/%m/%Y')}."

        elif action == "RENOVAR":
            book = await self.book_service.get_book_by_title(action_data["book_title"])
            if not book:
                return f"Lo siento, no se encontró el libro '{action_data['book_title']}'."
            
            reservation = await self.reservation_service.get_active_reservation_by_email_and_book(
                user_email=user_email,
                book_title=book.title
            )
            if not reservation:
                return f"No tienes una reserva activa para el libro '{book.title}'."
            
            new_end_date = datetime.utcnow() + timedelta(days=15)
            updated_reservation = await self.reservation_service.renew_reservation(
                reservation_id=reservation.id,
                new_end_date=new_end_date
            )
            return f"Has renovado exitosamente tu reserva del libro '{book.title}' hasta el {new_end_date.strftime('%d/%m/%Y')}."

        elif action == "ELIMINAR":
            success = await self.reservation_service.delete_reservation(
                user_email=user_email,
                book_title=action_data["book_title"]
            )
            if success:
                return f"Has eliminado exitosamente tu reserva del libro '{action_data['book_title']}'."
            else:
                return f"No tienes una reserva activa para el libro '{action_data['book_title']}'."

        elif action == "ELIMINAR_LIBRO":
            success = await self.book_service.delete_book_by_title(action_data["book_title"])
            if success:
                return f"El libro '{action_data['book_title']}' ha sido eliminado exitosamente de la biblioteca."
            else:
                return f"Lo siento, no se encontró el libro '{action_data['book_title']}'."

        elif action == "LISTAR":
            books = await self.book_service.get_all_books()
            if not books:
                return "No hay libros disponibles en la biblioteca."
            
            response = "Libros disponibles:\n\n"
            for book in books:
                status = "Disponible" if book.available else "Reservado"
                response += f"- {book.title} ({book.author}) - {status}\n"
            return response

        elif action == "CREAR":
            try:
                book_data = BookCreate(
                    title=action_data["book_title"],
                    author=action_data["book_author"],
                    isbn=action_data["book_isbn"],
                    publication_year=action_data["book_year"],
                    available=True
                )
                book = await self.book_service.create_book(book_data)
                return f"El libro '{book.title}' ha sido creado exitosamente en la biblioteca."
            except Exception as e:
                logger.error(f"Error al crear libro: {str(e)}")
                return "Lo siento, hubo un error al crear el libro. Por favor, verifica los datos proporcionados."

        else:
            return "Lo siento, no pude entender la acción solicitada. Por favor, intenta reformular tu solicitud."

    def __del__(self):

        if hasattr(self, 'db'):
            self.db.close() 