# 환경 변수 설정 관리 파일

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MODEL_PATH: str
    SCALER_PATH: str

    CORE_BANKING_DB_URL: str
    MYDATA_DB_URL: str

    class Config:
        env_file = ".env"

settings = Settings()