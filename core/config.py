import os
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """
    Класс для загрузки и валидации настроек из переменных окружения.
    """
    ollama_base_url: str = Field(..., env="OLLAMA_BASE_URL")
    ha_base_url: str = Field(..., env="HA_BASE_URL")
    ha_token: str = Field(..., env="HA_TOKEN")
    
    # ИЗМЕНЕНИЕ: Теперь читаем модель из .env
    ollama_model: str = Field(default="gemma3n:e2b", env="OLLAMA_MODEL")
    
    lancedb_path: str = "/app/lancedb_data"

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = 'ignore' 

settings = Settings()