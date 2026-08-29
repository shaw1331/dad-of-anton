from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    PROJECT_NAME: str = "Dad of Anton API"
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    
    # LLM Provider Configuration
    LLM_PROVIDER: str = "ollama"
    LLM_MODEL: str = "llama3"
    LLM_TEMPERATURE: float = 0.3
    LLM_TIMEOUT: int = 120
    
    GOOGLE_API_KEY: str = ""
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()