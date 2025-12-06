"""Configuration management for inwebstigate."""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration."""
    
    # LLM Configuration
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
    
    # Groq Configuration
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    # Ollama Configuration
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
    
    # Bright Data Proxy Configuration
    BRIGHT_DATA_USERNAME = os.getenv("BRIGHT_DATA_USERNAME", "")
    BRIGHT_DATA_PASSWORD = os.getenv("BRIGHT_DATA_PASSWORD", "")
    BRIGHT_DATA_HOST = os.getenv("BRIGHT_DATA_HOST", "")
    BRIGHT_DATA_PORT = os.getenv("BRIGHT_DATA_PORT", "")
    
    # Scraping Configuration
    MAX_NAVIGATION_DEPTH = int(os.getenv("MAX_NAVIGATION_DEPTH", "5"))
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
    PAGE_LOAD_TIMEOUT = int(os.getenv("PAGE_LOAD_TIMEOUT", "20"))
    
    @classmethod
    def use_proxy(cls):
        """Check if Bright Data proxy is configured."""
        return all([
            cls.BRIGHT_DATA_USERNAME,
            cls.BRIGHT_DATA_PASSWORD,
            cls.BRIGHT_DATA_HOST,
            cls.BRIGHT_DATA_PORT
        ])
    
    @classmethod
    def get_proxy_url(cls):
        """Get the proxy URL if configured."""
        if cls.use_proxy():
            return f"http://{cls.BRIGHT_DATA_USERNAME}:{cls.BRIGHT_DATA_PASSWORD}@{cls.BRIGHT_DATA_HOST}:{cls.BRIGHT_DATA_PORT}"
        return None

