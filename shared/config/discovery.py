from typing import Optional
from shared.config.base import BasePlatformSettings

class DiscoverySettings(BasePlatformSettings):
    """
    Typed configuration exclusively for the Data Ingestion (Discovery) service.
    """
    discovery_db_url: str
    
    tavily_api_key: Optional[str] = None
    firecrawler_api_key: Optional[str] = None
    adzuna_app_id: Optional[str] = None
    adzuna_api_key: Optional[str] = None
    
    class Config:
        env_prefix = "DISCOVERY_"
