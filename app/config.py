"""
Simplified Configuration management with Pydantic Settings
"""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, SecretStr


class Settings(BaseSettings):
    """Application settings"""
    
    # Environment
    ENVIRONMENT: str = Field("development", env="ENVIRONMENT")
    DEBUG: bool = Field(True, env="DEBUG")
    LOG_LEVEL: str = Field("DEBUG", env="LOG_LEVEL")
    
    # API
    API_V1_PREFIX: str = Field("/api/v1", env="API_V1_PREFIX")
    ALLOWED_HOSTS: List[str] = Field(["*"], env="ALLOWED_HOSTS")
    CORS_ORIGINS: List[str] = Field(
        ["http://localhost:3000", "http://localhost:8000"],
        env="CORS_ORIGINS"
    )
    
    # GCP (optional for local dev)
    GCP_PROJECT_ID: Optional[str] = Field(None, env="GCP_PROJECT_ID")
    GCP_REGION: str = Field("us-central1", env="GCP_REGION")
    
    # Vertex AI
    VEO_MODEL_NAME: str = Field(
        "veo-3.1-fast-generate-preview",
        env="VEO_MODEL_NAME"
    )
    GEMINI_MODEL_NAME: str = Field(
        "gemini-1.5-pro",
        env="GEMINI_MODEL_NAME"
    )
    
    # Cloud Storage
    STORAGE_BUCKET_NAME: Optional[str] = Field(None, env="STORAGE_BUCKET_NAME")
    
    # Firestore
    FIRESTORE_DATABASE: str = Field("(default)", env="FIRESTORE_DATABASE")
    
    # Security
    SECRET_KEY: str = Field("dev-secret-key-change-this", env="SECRET_KEY")
    ALGORITHM: str = Field("HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    
    # Stripe (optional for local dev)
    STRIPE_SECRET_KEY: Optional[str] = Field(None, env="STRIPE_SECRET_KEY")
    STRIPE_WEBHOOK_SECRET: Optional[str] = Field(None, env="STRIPE_WEBHOOK_SECRET")
    STRIPE_PRICE_ID: Optional[str] = Field(None, env="STRIPE_PRICE_ID")
    
    # Redis (optional)
    REDIS_URL: Optional[str] = Field(None, env="REDIS_URL")
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(10, env="RATE_LIMIT_PER_MINUTE")
    RATE_LIMIT_PER_DAY: int = Field(100, env="RATE_LIMIT_PER_DAY")
    
    # Video Limits
    MAX_VIDEO_DURATION: int = Field(30, env="MAX_VIDEO_DURATION")
    MIN_VIDEO_DURATION: int = Field(5, env="MIN_VIDEO_DURATION")
    MAX_CONCURRENT_JOBS: int = Field(3, env="MAX_CONCURRENT_JOBS")
    
    # Credits
    CREDITS_PER_VIDEO: int = Field(1, env="CREDITS_PER_VIDEO")
    CREDIT_PACKAGES: str = Field("10,50,100,500", env="CREDIT_PACKAGES")
    CREDIT_PRICES: str = Field("9.99,39.99,69.99,299.99", env="CREDIT_PRICES")
    
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields


# Create singleton
settings = Settings()