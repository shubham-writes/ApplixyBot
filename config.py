import os
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from .env file."""

    # Telegram
    TELEGRAM_BOT_TOKEN: str
    WEBHOOK_URL: str = ""  # Only needed in production

    # Database (Supabase PostgreSQL)
    DATABASE_URL: str

    # AI — NVIDIA NIM API
    NVIDIA_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
    NVIDIA_API_KEY_70B: str
    NVIDIA_API_KEY_8B: str
    NVIDIA_MODEL_70B: str = "meta/llama3-70b-instruct"
    NVIDIA_MODEL_8B: str = "meta/llama3-8b-instruct"

    # Payments — Razorpay
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""

    # App Config
    ENVIRONMENT: str = "development"
    MAX_COVER_LETTERS_FREE: int = 3


    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# Singleton settings instance
settings = Settings()
