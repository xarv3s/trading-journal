from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache

class Settings(BaseSettings):
    PROJECT_NAME: str = "Trading Journal API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    SUPABASE_URL: str
    
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Kite Connect
    KITE_API_KEY: str = Field(alias="ZERODHA_API_KEY")
    KITE_API_SECRET: str = Field(alias="ZERODHA_API_SECRET")
    KITE_REDIRECT_URL: str = "http://localhost:8000/api/v1/login/callback"
    


    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore" # Allow extra fields like OPENAI_API_KEY

@lru_cache()
def get_settings():
    return Settings()
