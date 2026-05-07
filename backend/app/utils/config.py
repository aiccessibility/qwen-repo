from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    APP_NAME: str = "Accessibility Multi-Agent Platform"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/accessibility_db"
    DATABASE_ASYNC_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/accessibility_db"
    
    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    
    # LLM / AI
    LLM_PROVIDER: str = "ollama"  # ollama, vllm, openai-compatible
    LLM_BASE_URL: str = "http://ollama:11434"
    LLM_MODEL_AUDITOR: str = "llama2:70b"  # Powerful model for auditing
    LLM_MODEL_MONITOR: str = "llama2:13b"  # Lighter model for monitoring
    LLM_MODEL_REPORTER: str = "llama2:70b"  # Powerful model for reports
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Storage
    STORAGE_TYPE: str = "local"  # local, s3
    STORAGE_PATH: str = "/app/storage"
    S3_BUCKET: Optional[str] = None
    S3_ENDPOINT: Optional[str] = None
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None
    
    # Celery
    CELERY_BROKER_URL: str = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"
    
    # WCAG Standards
    WCAG_LEVEL: str = "AA"  # A, AA, AAA
    WCAG_VERSION: str = "2.2"  # 2.1, 2.2
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
