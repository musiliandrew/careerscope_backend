from typing import Optional
from shared.config.base import BasePlatformSettings

class PersonalizationSettings(BasePlatformSettings):
    """
    Typed configuration exclusively for the Personalization (Memory) service.
    """
    qdrant_endpoint: str
    qdrant_api_key: Optional[str] = None
    
    embedding_model_key: Optional[str] = None
    
    class Config:
        env_prefix = "MEMORY_"
