from pydantic_settings import BaseSettings, SettingsConfigDict

class BasePlatformSettings(BaseSettings):
    """
    Base configuration for all CareerScope services.
    Enforces that services load settings through Pydantic instead of os.getenv().
    """
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    environment: str = "development"
    log_level: str = "INFO"
