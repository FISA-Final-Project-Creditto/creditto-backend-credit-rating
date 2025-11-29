from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MODEL_PATH: str
    SCALER_PATH: str

    CORE_BANKING_DB_URL: str
    CORE_BANKING_READ_DB_URL: Optional[str] = None
    MYDATA_DB_URL: str
    MYDATA_READ_DB_URL: Optional[str] = None

    class Config:
        env_file = ".env"

settings = Settings()
