from typing import Optional
from shared.config.base import BasePlatformSettings

class BackendSettings(BasePlatformSettings):
    """
    Typed configuration exclusively for the State (Backend) service.
    """
    database_url: str
    secret_key: str
    
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    
    github_id: Optional[str] = None
    github_secret: Optional[str] = None
    
    backblaze_keyid: Optional[str] = None
    backblaze_applicationkey: Optional[str] = None
    
    class Config:
        env_prefix = "BACKEND_"
