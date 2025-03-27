from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    # API paths
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@db:5432/bittensor_db")
    
    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    
    # API Key
    API_KEY: str = os.getenv("API_KEY", "your_test_api_key")
    
    # Cache TTL in seconds (2 minutes)
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "120"))
    
    # Task status TTL in seconds (1 hour)
    TASK_STATUS_TTL: int = int(os.getenv("TASK_STATUS_TTL", "3600"))
    
    # API Keys for external services
    DATURA_API_KEY: str = os.getenv("DATURA_API_KEY", "your_datura_api_key")
    CHUTES_API_KEY: str = os.getenv("CHUTES_API_KEY", "your_chutes_api_key")
    
    # Bittensor settings
    BITTENSOR_CHAIN_ENDPOINT: str = os.getenv("BITTENSOR_CHAIN_ENDPOINT", "ws://test.finney.opentensor.ai:9944")
    BITTENSOR_WALLET_MNEMONIC: str = os.getenv("BITTENSOR_WALLET_MNEMONIC", "your_mnemonic_here")
    
    # Bittensor defaults
    default_netuid: str = os.getenv("DEFAULT_NETUID", "18")
    default_hotkey: str = os.getenv("DEFAULT_HOTKEY", "5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v")
    
    # Configuration for Pydantic V2
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"  # Ignore extra fields
    )

settings = Settings()