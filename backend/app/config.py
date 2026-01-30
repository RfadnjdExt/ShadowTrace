"""
Application configuration using Pydantic Settings
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )
    
    # Database
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/shadowtrace"
    database_url_sync: str = "postgresql://postgres:password@localhost:5432/shadowtrace"
    
    # Gemini API (mock by default for development)
    gemini_api_key: str = "mock-api-key"
    gemini_model: str = "gemini-2.0-flash"
    use_mock_ai: bool = True
    
    # Application
    debug: bool = True


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
