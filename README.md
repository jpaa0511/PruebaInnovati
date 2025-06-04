# Biblioteca API

API REST para gestión de biblioteca desarrollada con FastAPI y PostgreSQL.

## Requisitos Previos

- Python 3.11.6 - IMPORTANTE: POR COMPATIBILIDAD DE DEPENDENCIAS
- PostgreSQL 15 o superior
- Git

## Configuración del Entorno

1. Abre una consola de gitBash para clonar el repositorio:
```bash
git clone https://github.com/jpaa0511/PruebaInnovati.git
cd PruebaInnovati
```

2. Configurar el entorno virtual:
```bash
# Borrar entorno actual para evitar problemas
rm -rf venv
```
```bash
# Crear nuevo entorno virtual
python -m venv venv
```
```bash
# Activar el entorno virtual
source venv/Scripts/activate
```

3. Instalar dependencias:
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Configuración de la Base de Datos

1. Instalar PostgreSQL si no está instalado:
   - Descargar e instalar desde [postgresql.org](https://www.python.org/downloads/release/python-3116/)
   - Durante la instalación, recuerda la contraseña de postgres y el puerto que configuraste.

2. Abre PgAdmin o el gestor de db que uses para crear la base de datos:
```sql
CREATE DATABASE biblioteca;
```
3. Dentro del archivo .env, configura la variable DATABASE_URL con el siguiente formato:

```bash
# Recuerda quitar las "<>"
DATABASE_URL=postgresql://<usuario>:<contraseña>@localhost:<puerto>/biblioteca 
```
Reemplaza los valores según tu configuración local:
- usuario: nombre de usuario de PostgreSQL
- contraseña: contraseña del usuario
- puerto: puerto donde se ejecuta PostgreSQL (por defecto 5432)
- biblioteca: nombre de la base de datos del proyecto

4. Inicializar base de datos:

```bash
python -m app.db.init_db 
```
## Ejecutar la Aplicación

1. Iniciar el servidor de desarrollo:
```bash
uvicorn app.main:app --reload
```

La API estará disponible en: http://localhost:8000

## Documentación de la API

- Documentación Swagger UI: http://localhost:8000/docs
- Documentación ReDoc: http://localhost:8000/redoc

## Estructura del Proyecto

```
BibliotecaAPI/
├── app/
│   ├── main.py
│   ├── models/
│   ├── schemas/
│   └── routers/
├── venv/
├── requirements.txt
├── .env
└── README.md
```

## Despliegue

No fue posible debido a la falta de acceso a una cuenta azure con licencia.

NOTA: La dockerización del proyecto estaba planificada para simplificar el proceso de despliegue, pero no se alcanzó a implementar debido a limitaciones de tiempo.

