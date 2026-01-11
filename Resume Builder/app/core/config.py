from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path("/app") if Path("/app").exists() else Path(__file__).resolve().parents[3]

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    # Ollama (legacy) - kept optional for backwards compatibility
    OLLAMA_HOST: str | None = None
    OLLAMA_MODEL: str | None = None

    # OpenAI configuration
    OPENAI_API_KEY: str
    OPENAI_API_BASE: str = "https://api.openai.com"
    OPENAI_MODEL: str = "gpt-3.5-turbo"

    ALGORITHM: str
    STRIPE_API_KEY: str
    PRO_PRICE_ID: str
    PRO_PLUS_PRICE_ID: str
    FRONTEND_URL: str

    MAILGUN_DOMAIN: str
    MAILGUN_API_KEY: str
    MAILGUN_BASE_URL: str   
    SMTP_USER: str
    

    STRIPE_WEBHOOK_SECRET: str
    TEX_BIN: str

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()
