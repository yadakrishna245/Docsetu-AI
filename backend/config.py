"""
DocSetu AI - Configuration Module
Uses Pydantic BaseSettings for type-safe configuration management.
"""

from typing import List
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "DocSetu AI"
    app_env: str = "development"
    debug: bool = True
    secret_key: str = "change-this-in-production"
    api_version: str = "v1"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    database_url: str = "sqlite:///./docsetu.db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4"

    # Google Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-pro"

    # LLM Provider
    llm_provider: str = "openai"

    # JWT Authentication
    jwt_secret_key: str = "change-this-jwt-secret"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60

    # File Upload
    upload_dir: str = "./uploads"
    max_file_size_mb: int = 50
    allowed_extensions: str = "pdf,png,jpg,jpeg,tiff,bmp"

    # OCR Configuration
    tesseract_cmd: str = "tesseract"
    tesseract_lang: str = "eng+hin+tam+tel+kan"

    # ChromaDB
    chroma_persist_dir: str = "./chroma_db"

    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    # Razorpay Payment Gateway
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""

    # SMTP Email
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "noreply@docsetu.ai"
    app_base_url: str = "http://localhost:3000"

    # Logging
    log_level: str = "INFO"
    log_file: str = "./logs/docsetu.log"

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    @property
    def allowed_extensions_list(self) -> List[str]:
        """Get allowed extensions as a list."""
        return [ext.strip() for ext in self.allowed_extensions.split(",")]

    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def max_file_size_bytes(self) -> int:
        """Get max file size in bytes."""
        return self.max_file_size_mb * 1024 * 1024

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.app_env == "production"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
