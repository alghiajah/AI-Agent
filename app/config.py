import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    openrouter_api_key: str = Field(..., alias="OPENROUTER_API_KEY")
    gemini_api_key: str = Field(..., alias="GEMINI_API_KEY")
    
    supervisor_model: str = Field("deepseek/deepseek-chat", alias="SUPERVISOR_MODEL")
    researcher_model: str = Field("gemini-1.5-pro", alias="RESEARCHER_MODEL")
    writer_model: str = Field("openai/gpt-4o", alias="WRITER_MODEL")
    
    host: str = Field("0.0.0.0", alias="HOST")
    port: int = Field(8000, alias="PORT")
    debug: bool = Field(True, alias="DEBUG")
    
    # Global settings
    request_timeout: float = 120.0  # Timeouts for external API requests (in seconds)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Instantiate settings singleton
settings = Settings()
