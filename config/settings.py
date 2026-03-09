"""
Configuración centralizada — lee variables de entorno
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Base de datos
    DATABASE_URL: str

    # Anthropic
    ANTHROPIC_API_KEY: str

    # Gmail
    GMAIL_ACCOUNT_EMAIL: str
    GOOGLE_CREDENTIALS_JSON: str = ""  # base64 del credentials.json, para Railway

    # Google Sheets
    GOOGLE_SHEETS_ID: str

    # Telegram
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_ADMIN_CHAT_ID: str

    # App
    APP_ENV: str = "development"
    SECRET_KEY: str = "dev-secret-key"
    APP_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:3000"

    # Polling
    GMAIL_POLL_INTERVAL: int = 120

    # Negocio
    BUSINESS_NAME: str = "Servicio Técnico"
    BUSINESS_PHONE: str = ""
    BUSINESS_HOURS: str = "Lunes a Viernes 9:00-18:00"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
