from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config.config import settings


engine = create_engine(settings.MYDATA_DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_mydata_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()