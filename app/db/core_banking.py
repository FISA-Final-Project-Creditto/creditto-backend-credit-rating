from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config.config import settings


engine = create_engine(settings.CORE_BANKING_DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_core_banking_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()