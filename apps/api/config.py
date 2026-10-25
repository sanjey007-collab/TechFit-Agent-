import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"
    DATABASE_URL: str = "sqlite+aiosqlite:///./techfit.db"

    # Mock Store Integration
    MOCK_STORE_URL: str = "http://localhost:8001"
    MOCK_STORE_SERVICE_TOKEN: str = "techfit_sec_token_a984b2c1f0e478d1"

    # Admin key for config status
    ADMIN_API_KEY: str = "techfit_admin_secret_4892bc01ef3a7719"

    # Key 1: Search Provider
    SEARCH_PROVIDER: str = "serper"
    SEARCH_API_KEY: str = ""
    GOOGLE_SEARCH_API_KEY: str = ""
    GOOGLE_SEARCH_ENGINE_ID: str = ""

    # Key 2: Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash"

    # Key 3: Product Details
    PRODUCT_DETAILS_PROVIDER: str = "serpapi"
    PRODUCT_DETAILS_API_KEY: str = ""
    PRODUCT_DETAILS_BASE_URL: str = ""

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def mock_store_base_url(self) -> str:
        url = self.MOCK_STORE_URL.strip()
        if url and not url.startswith("http://") and not url.startswith("https://"):
            return f"https://{url}"
        return url

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
