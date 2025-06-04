from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.book import Base as BookBase
from app.models.reservation import Base as ReservationBase

def init_db():
    engine = create_engine(settings.DATABASE_URL)
    
    BookBase.metadata.create_all(bind=engine)
    ReservationBase.metadata.create_all(bind=engine)
    
    print("Base de datos inicializada correctamente!")

if __name__ == "__main__":
    init_db() 