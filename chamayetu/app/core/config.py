"""
Application configuration using Pydantic Settings.
Loads environment variables from .env file.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "ChamaYetu"
    APP_ENV: str = "development"  # development | production
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Database
    DATABASE_URL: str

    # Redis + Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # M-Pesa Daraja
    MPESA_ENV: str = "sandbox"  # sandbox | production
    MPESA_CONSUMER_KEY: str
    MPESA_CONSUMER_SECRET: str
    MPESA_SHORTCODE: str = "174379"
    MPESA_PASSKEY: str
    MPESA_B2C_SHORTCODE: str = "600000"
    MPESA_INITIATOR_NAME: str = "testapi"
    MPESA_INITIATOR_PASSWORD: str

    # Callback URLs
    MPESA_STK_CALLBACK_URL: Optional[str] = None
    MPESA_B2C_RESULT_URL: Optional[str] = None
    MPESA_B2C_TIMEOUT_URL: Optional[str] = None

    # Admin Dashboard Credentials
    ADMIN_DASHBOARD_EMAIL: str = "admin@chamayetu.com"
    ADMIN_DASHBOARD_PASSWORD: str = "AdminPassword123!"

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
