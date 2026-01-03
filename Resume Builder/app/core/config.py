from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    OLLAMA_HOST: str
    OLLAMA_MODEL: str
    ALGORITHM: str
    STRIPE_API_KEY: str
    PRO_PRICE_ID: str
    PRO_PLUS_PRICE_ID: str
    FRONTEND_URL: str 
    SMTP_HOST: str
    SMTP_PORT: str
    SMTP_USER: str
    SMTP_PASS: str
    STRIPE_WEBHOOK_SECRET: str
    TEX_BIN: str = "xelatex"

    class Config:
        # Resolve .env relative to package root to work regardless of CWD
        env_file = str(Path(__file__).resolve().parents[1] / ".env")
        extra = "ignore"  # Ignore any unknown env vars
        

settings = Settings()