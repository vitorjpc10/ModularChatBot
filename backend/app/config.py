"""
Configuration management for the Modular Chatbot application.
Uses python-decouple for environment variable management.
"""

from decouple import config, Csv
from typing import Optional
import logging


class Settings:
    """Application settings loaded from environment variables."""
    
    # Application Settings
    APP_NAME: str = config("APP_NAME", default="ModularChatBot")
    DEBUG: bool = config("DEBUG", default=True, cast=bool)
    ENVIRONMENT: str = config("ENVIRONMENT", default="development")
    
    # Server Settings
    HOST: str = config("HOST", default="0.0.0.0")
    PORT: int = config("PORT", default=8000, cast=int)
    
    # Database Settings
    DATABASE_URL: str = config("DATABASE_URL", default="sqlite:///./chatbot.db")
    TEST_DATABASE_URL: str = config("TEST_DATABASE_URL", default="sqlite:///./test_chatbot.db")
    
    # Redis Settings (for future use)
    REDIS_URL: str = config("REDIS_URL", default="redis://localhost:6379")
    REDIS_DB: int = config("REDIS_DB", default=0, cast=int)
    
    # AI/LLM Settings
    GROQ_API_KEY: str = config("GROQ_API_KEY", default="")
    GROQ_MODEL: str = config("GROQ_MODEL", default="llama3-70b-8192")
    
    # Security Settings
    SECRET_KEY: str = config("SECRET_KEY", default="your-secret-key-here-change-in-production")
    ALGORITHM: str = config("ALGORITHM", default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = config("ACCESS_TOKEN_EXPIRE_MINUTES", default=30, cast=int)
    
    # Logging
    LOG_LEVEL: str = config("LOG_LEVEL", default="INFO")
    LOG_FORMAT: str = config("LOG_FORMAT", default="json")
    
    # External APIs
    INFINITEPAY_HELP_URL: str = config("INFINITEPAY_HELP_URL", default="https://ajuda.infinitepay.io/pt-BR/")
    
    @classmethod
    def validate(cls) -> None:
        """Validate required configuration settings."""
        required_settings = [
            ("GROQ_API_KEY", cls.GROQ_API_KEY),
        ]
        
        missing_settings = []
        for name, value in required_settings:
            if not value:
                missing_settings.append(name)
        
        if missing_settings:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_settings)}")
    
    @classmethod
    def get_logging_config(cls) -> dict:
        """Get logging configuration."""
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                    "format": "%(asctime)s %(levelname)s %(name)s %(message)s"
                },
                "standard": {
                    "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
                }
            },
            "handlers": {
                "default": {
                    "level": cls.LOG_LEVEL,
                    "formatter": cls.LOG_FORMAT if cls.LOG_FORMAT == "json" else "standard",
                    "class": "logging.StreamHandler",
                }
            },
            "loggers": {
                "": {
                    "handlers": ["default"],
                    "level": cls.LOG_LEVEL,
                    "propagate": False
                }
            }
        }


# Global settings instance
settings = Settings()

# Validate settings on import
try:
    settings.validate()
except ValueError as e:
    logging.error(f"Configuration validation failed: {e}")
    raise
