from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config.config import settings


write_engine = create_engine(settings.CORE_BANKING_DB_URL, pool_pre_ping=True)
read_engine = create_engine(
    settings.CORE_BANKING_READ_DB_URL or settings.CORE_BANKING_DB_URL,
    pool_pre_ping=True,
)

WriteSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=write_engine)
ReadSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=read_engine)


def get_core_banking_write_db():
    db = WriteSessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_core_banking_read_db():
    db = ReadSessionLocal()
    try:
        yield db
    finally:
        db.close()
