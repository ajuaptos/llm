"""
Configuration management for Local-AI-RAG application
"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "Local-AI-RAG"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Ollama Configuration
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MAIN_MODEL: str = "llama3.2:3b"
    OLLAMA_SCOUT_MODEL: str = "llama3.2:1b"
    OLLAMA_TIMEOUT: int = 120
    
    # Embeddings Configuration
    EMBEDDING_PROVIDER: str = "ollama"  # "ollama" or "sentence-transformers"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"
    SENTENCE_TRANSFORMER_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 768
    
    # Vector Database
    VECTOR_DB_TYPE: str = "chromadb"  # "chromadb" or "sqlite"
    CHROMA_PERSIST_DIRECTORY: str = "./data/chroma"
    
    # SQLite Database
    DATABASE_PATH: str = "./data/app.db"
    
    # Google Custom Search API
    GOOGLE_API_KEY: Optional[str] = None
    GOOGLE_CSE_ID: Optional[str] = None
    SEARCH_MAX_RESULTS: int = 5
    USE_WEB_SCRAPING_FALLBACK: bool = True  # Enable web scraping when API not configured
    
    # RAG Configuration
    RAG_TOP_K: int = 5
    RAG_SIMILARITY_THRESHOLD: float = 0.5
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    
    # Scout Configuration
    SCOUT_UNCERTAINTY_THRESHOLD: float = 0.6
    SCOUT_ENABLED: bool = True
    
    # AI Firewall Configuration
    FIREWALL_ENABLED: bool = True
    FIREWALL_BLOCKED_CATEGORIES: list = [
        "harmful", "hateful", "racist", "sexist", "violent", "illegal"
    ]
    
    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8000"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


def ensure_directories():
    """Ensure required directories exist"""
    settings = get_settings()
    
    # Create data directory
    data_dir = Path("./data")
    data_dir.mkdir(exist_ok=True)
    
    # Create chroma directory if using ChromaDB
    if settings.VECTOR_DB_TYPE == "chromadb":
        chroma_dir = Path(settings.CHROMA_PERSIST_DIRECTORY)
        chroma_dir.mkdir(parents=True, exist_ok=True)


# Initialize directories on import
ensure_directories()
