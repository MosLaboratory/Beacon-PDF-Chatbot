"""
Configuration settings for the PDF Chatbot application.
"""

import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = "your_openai_api_key_here"
    
    # Application Configuration
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    
    # CORS Configuration
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    
    # Model Configuration
    DEFAULT_MODEL: str = "gpt-3.5-turbo"
    MAX_TOKENS: int = 1000
    TEMPERATURE: float = 0.7
    
    # Weaviate Configuration
    WEAVIATE_URL: str = "http://localhost:8080"
    WEAVIATE_API_KEY: str = ""
    WEAVIATE_CLASS_NAME: str = "PDFChunks"
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Get ALLOWED_ORIGINS as a list."""
        if isinstance(self.ALLOWED_ORIGINS, str):
            return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(',')]
        return self.ALLOWED_ORIGINS
    
    def validate(self):
        """Validate required settings."""
        # Remove quotes if present
        api_key = self.OPENAI_API_KEY.strip('"\'')
        
        print(f"DEBUG: API key length: {len(api_key)}")
        print(f"DEBUG: API key starts with 'sk-': {api_key.startswith('sk-')}")
        print(f"DEBUG: API key is empty: {not api_key}")
        print(f"DEBUG: API key equals default: {api_key == 'your_openai_api_key_here'}")
        
        if not api_key or api_key == "your_openai_api_key_here":
            raise ValueError("OPENAI_API_KEY must be set to a valid OpenAI API key")
        
        if not api_key.startswith("sk-"):
            raise ValueError("OPENAI_API_KEY must be a valid OpenAI API key starting with 'sk-'")

# Create settings instance
settings = Settings() 