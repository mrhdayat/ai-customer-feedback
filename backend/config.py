from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Supabase (Required)
    supabase_url: str
    supabase_anon_key: str  
    supabase_service_role_key: str
    
    # AI Services (Optional - akan disable features jika tidak ada)
    huggingface_api_token: Optional[str] = None
    ibm_watson_nlu_api_key: Optional[str] = None
    ibm_watson_nlu_url: str = "https://api.us-south.natural-language-understanding.watson.cloud.ibm.com"
    replicate_api_token: Optional[str] = None
    ibm_orchestrate_api_key: Optional[str] = None
    ibm_orchestrate_base_url: str = "https://dl.watson-orchestrate.ibm.com"
    
    # Backend  
    backend_secret_key: str = "default-secret-key-change-in-production-min-32-chars"
    backend_algorithm: str = "HS256"
    backend_access_token_expire_minutes: int = 30
    
    # Rate limiting
    rate_limit_per_minute: int = 60
    
    # CORS
    frontend_url: str = "http://localhost:3000"
    
    # Environment
    environment: str = "development"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
