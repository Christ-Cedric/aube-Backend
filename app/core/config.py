from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, validator

class Settings(BaseSettings):
    # Base
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: List[AnyHttpUrl] = []

    # Database
    MONGODB_URI: str = "mongodb://localhost:27017/subscription_db"
    MONGODB_DATABASE: str = "subscription_db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/1"
    REDIS_CACHE_TTL_SECONDS: int = 300

    # Security
    JWT_SECRET_KEY: str = "default_secret_key_for_dev_only"
    JWT_ALGORITHM: str = "HS256"
    
    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30
    WS_RECONNECT_DELAY: int = 5
    
    # Background Tasks
    EXPIRATION_CHECK_INTERVAL_HOURS: int = 1
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100

    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
