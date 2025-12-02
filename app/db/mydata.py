from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config.config import settings


read_engine = create_engine(
    settings.MYDATA_READ_DB_URL or settings.MYDATA_DB_URL,
    pool_pre_ping=True,
)
ReadSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=read_engine)


def get_mydata_read_db():
    db = ReadSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Backwards compatibility for existing imports
get_mydata_db = get_mydata_read_db
