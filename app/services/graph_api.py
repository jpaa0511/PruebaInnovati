from typing import List, Optional
from datetime import datetime, timedelta
from msgraph.core import GraphClient
from azure.identity import ClientSecretCredential
from app.core.config import settings
from app.core.graph_config import GraphSettings
import logging
import asyncio
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GraphAPIService:

    def __init__(self):
        self.settings = GraphSettings()
        logger.info("Inicializando GraphAPIService con las siguientes credenciales:")
        logger.info(f"Tenant ID: {self.settings.AZURE_TENANT_ID}")
        logger.info(f"Client ID: {self.settings.AZURE_CLIENT_ID}")
        logger.info(f"Email: {self.settings.EMAIL_ADDRESS}")
        
        self.scopes = [
            "https://graph.microsoft.com/.default"
        ]
        
        try:
            self.credential = ClientSecretCredential(
                tenant_id=self.settings.AZURE_TENANT_ID,
                client_id=self.settings.AZURE_CLIENT_ID,
                client_secret=self.settings.AZURE_CLIENT_SECRET
            )
            
            token = self.credential.get_token(self.scopes[0])
            logger.info("Token obtenido exitosamente")
            logger.info(f"Token expira en: {token.expires_on}")
            
            self.client = GraphClient(credential=self.credential)
            self.email_address = self.settings.EMAIL_ADDRESS
            logger.info(f"GraphAPIService inicializado para {self.email_address}")
            
        except Exception as e:
            logger.error(f"Error al inicializar GraphAPIService: {str(e)}")
            raise

    async def _get_valid_token(self):

        try:
            token = self.credential.get_token(self.scopes[0])
            logger.info("Token obtenido exitosamente")
            logger.info(f"Token expira en: {token.expires_on}")
            return token
        except Exception as e:
            logger.error(f"Error al obtener token: {str(e)}")
            raise

    async def get_unread_emails(self, last_check_time: Optional[datetime] = None) -> List[dict]:

        try:
            logger.info("Obteniendo correos no leídos...")
            
            if not last_check_time:
                last_check_time = datetime.utcnow() - timedelta(hours=24)

            filter_date = last_check_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            logger.info(f"Buscando correos desde {filter_date}")

            await self._get_valid_token()

            endpoint = f"/users/{self.email_address}/messages"
            params = {
                "$filter": f"receivedDateTime ge {filter_date} and isRead eq false",
                "$select": "id,subject,body,from,receivedDateTime",
                "$orderby": "receivedDateTime desc",
                "$top": 10
            }
            
            logger.info(f"Endpoint: {endpoint}")
            logger.info(f"Parámetros de búsqueda: {params}")

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.get(endpoint, params=params)
            )
            
            if response.status_code == 200:
                emails = response.json().get('value', [])
                logger.info(f"Se encontraron {len(emails)} correos no leídos")
                for email in emails:
                    logger.info(f"Correo encontrado - Asunto: {email.get('subject')}, De: {email.get('from', {}).get('emailAddress', {}).get('address')}")
                return emails
            else:
                logger.error(f"Error al obtener correos. Código de estado: {response.status_code}")
                logger.error(f"Respuesta: {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error al obtener correos no leídos: {str(e)}")
            return []

    async def send_email(self, to: str, subject: str, body: str) -> bool:

        try:
            logger.info(f"Enviando correo a {to}")
            
            await self._get_valid_token()

            message = {
                "message": {
                    "subject": subject,
                    "body": {
                        "contentType": "HTML",
                        "content": body
                    },
                    "toRecipients": [
                        {
                            "emailAddress": {
                                "address": to
                            }
                        }
                    ]
                }
            }
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.post(
                    f"/users/{self.email_address}/sendMail",
                    json=message
                )
            )
            
            success = response.status_code == 202
            if success:
                logger.info(f"Correo enviado exitosamente a {to}")
            else:
                logger.error(f"Error al enviar correo a {to}: {response.status_code}")
                try:
                    error_details = response.json()
                    logger.error(f"Detalles del error: {json.dumps(error_details, indent=2)}")
                except:
                    logger.error(f"Respuesta: {response.text}")
                    logger.error(f"URL: {response.url}")
            return success
        except Exception as e:
            logger.error(f"Error al enviar correo: {str(e)}")
            return False

    async def mark_email_as_read(self, email_id: str) -> bool:

        try:
            logger.info(f"Marcando correo {email_id} como leído")
            
            await self._get_valid_token()

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.patch(
                    f"/users/{self.email_address}/messages/{email_id}",
                    json={"isRead": True}
                )
            )
            
            success = response.status_code == 200
            if success:
                logger.info(f"Correo {email_id} marcado como leído")
            else:
                logger.error(f"Error al marcar correo como leído: {response.status_code}")
                try:
                    error_details = response.json()
                    logger.error(f"Detalles del error: {json.dumps(error_details, indent=2)}")
                except:
                    logger.error(f"Respuesta: {response.text}")
                    logger.error(f"URL: {response.url}")
            return success
        except Exception as e:
            logger.error(f"Error al marcar correo como leído: {str(e)}")
            return False 