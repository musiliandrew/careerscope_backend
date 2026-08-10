import os
from typing import Optional
from pydantic import Field
from shared.config.base import BasePlatformSettings

class DecisionSettings(BasePlatformSettings):
    """
    Typed configuration exclusively for the Decision Engine.
    """
    gemini_api_key: str = Field(default_factory=lambda: os.getenv("DECISION_GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY") or "mock_key")
    openrouter_api_key: Optional[str] = None
    ollama_base_url: Optional[str] = None
    
    langfuse_public_key: Optional[str] = None
    langfuse_secret_key: Optional[str] = None
    langfuse_host: str = "https://cloud.langfuse.com"
    
    ai_primary: str = "gemini"
    ai_fallback: Optional[str] = None
    
    class Config:
        env_prefix = "DECISION_"
        extra = "ignore" # expects DECISION_GEMINI_API_KEY in .env
