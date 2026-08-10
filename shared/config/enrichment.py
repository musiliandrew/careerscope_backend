from typing import Optional
from shared.config.base import BasePlatformSettings

class EnrichmentSettings(BasePlatformSettings):
    """
    Typed configuration exclusively for the AI Enrichment (Knowledge) service.
    """
    knowledge_db_url: str
    
    gemini_api_key: str
    openrouter_api_key: Optional[str] = None
    
    langfuse_public_key: Optional[str] = None
    langfuse_secret_key: Optional[str] = None
    langfuse_host: str = "https://cloud.langfuse.com"
    
    class Config:
        env_prefix = "KNOWLEDGE_"
