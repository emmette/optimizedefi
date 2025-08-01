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
        default=["http://localhost:3000", "http://localhost:3001", "http://localhost:8000"],
        env="ALLOWED_ORIGINS"
    )
    
    # 1inch API
    ONEINCH_API_KEY: str = Field(default="", env="ONEINCH_API_KEY")
    ONEINCH_BASE_URL: str = Field(default="https://api.1inch.io/v6.0", env="ONEINCH_BASE_URL")
    
    # Alchemy API
    ALCHEMY_API_KEY: str = Field(default="", env="ALCHEMY_API_KEY")
    
    # Authentication
    SECRET_KEY: str = Field(default="your-secret-key-here-change-in-production", env="SECRET_KEY")
    JWT_SECRET: str = Field(default="your-secret-key-here", env="JWT_SECRET")
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    JWT_EXPIRATION_HOURS: int = Field(default=24, env="JWT_EXPIRATION_HOURS")
    
    # Chain IDs
    SUPPORTED_CHAINS: List[int] = Field(
        default=[
            1,        # Ethereum
            137,      # Polygon
            42161,    # Arbitrum One
            42170,    # Arbitrum Nova
            10,       # Optimism
            8453,     # Base
            1101,     # Polygon zkEVM
            810180,   # World Chain
            7777777   # Zora
        ],
        env="SUPPORTED_CHAINS"
    )
    
    # OpenRouter Configuration
    OPENROUTER_API_KEY: str = Field(default="", env="OPENROUTER_API_KEY")
    OPENROUTER_BASE_URL: str = Field(
        default="https://openrouter.ai/api/v1",
        env="OPENROUTER_BASE_URL"
    )
    DEFAULT_MODEL: str = Field(default="google/gemini-2.0-flash", env="DEFAULT_MODEL")
    PORTFOLIO_AGENT_MODEL: str = Field(
        default="google/gemini-2.0-flash",
        env="PORTFOLIO_AGENT_MODEL"
    )
    REBALANCING_AGENT_MODEL: str = Field(
        default="openai/gpt-4o",
        env="REBALANCING_AGENT_MODEL"
    )
    SWAP_AGENT_MODEL: str = Field(
        default="google/gemini-2.0-flash",
        env="SWAP_AGENT_MODEL"
    )
    GENERAL_AGENT_MODEL: str = Field(
        default="google/gemini-2.0-flash",
        env="GENERAL_AGENT_MODEL"
    )
    
    # Metrics Configuration
    ENABLE_METRICS: bool = Field(default=True, env="ENABLE_METRICS")
    
    # Admin Configuration
    ADMIN_WALLET_ADDRESSES: List[str] = Field(
        default=[],
        env="ADMIN_WALLET_ADDRESSES"
    )
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True
    }

settings = Settings()