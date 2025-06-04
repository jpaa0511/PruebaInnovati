from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.api_v1.api import api_router
import asyncio
import logging
from app.tasks.email_checker import check_emails

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

azure_logger = logging.getLogger('azure')
azure_logger.setLevel(logging.WARNING)

httpx_logger = logging.getLogger('httpx')
httpx_logger.setLevel(logging.WARNING)

app = FastAPI(
    title="Biblioteca API",
    description="API para gestión de biblioteca mediante correo electrónico",
    version="1.0.0",
    openapi_url="/api/v1/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "message": "Bienvenido a la API de la Biblioteca",
        "version": "1.0.0",
        "docs_url": "/docs"
    }

@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy"}

email_checker_task = None

async def run_email_checker():
    while True:
        try:
            await check_emails()
            await asyncio.sleep(30)
        except Exception as e:
            logger.error(f"Error en el verificador de correos: {str(e)}")
            await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    global email_checker_task
    logger.info("Iniciando verificador de correos...")
    email_checker_task = asyncio.create_task(run_email_checker())

@app.on_event("shutdown")
async def shutdown_event():
    global email_checker_task
    if email_checker_task:
        logger.info("Deteniendo verificador de correos...")
        email_checker_task.cancel()
        try:
            await email_checker_task
        except asyncio.CancelledError:
            pass 