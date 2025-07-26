from pydantic import Field
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Application
    HOST: str = Field(default="0.0.0.0", env="BACKEND_HOST")
    PORT: int = Field(default=8000, env="BACKEND_PORT")
    DEBUG: bool = Field(default=True, env="DEBUG")
    
    # CORS
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        env="ALLOWED_ORIGINS"
    )
    
    # 1inch API
    ONEINCH_API_KEY: str = Field(default="", env="ONEINCH_API_KEY")
    ONEINCH_BASE_URL: str = Field(default="https://api.1inch.io/v6.0", env="ONEINCH_BASE_URL")
    
    # Authentication
    JWT_SECRET: str = Field(default="your-secret-key-here", env="JWT_SECRET")
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    JWT_EXPIRATION_HOURS: int = Field(default=24, env="JWT_EXPIRATION_HOURS")
    
    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    # Chain IDs
    SUPPORTED_CHAINS: List[int] = Field(
        default=[1, 137, 10, 42161],  # Ethereum, Polygon, Optimism, Arbitrum
        env="SUPPORTED_CHAINS"
    )
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True
    }

settings = Settings()