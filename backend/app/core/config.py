"""
Application Configuration
Loads settings from environment variables with Azure AI Foundry SDK support
"""
from typing import List, Union, Any
from pydantic import field_validator
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Project
    PROJECT_NAME: str = "Market Research Assistant"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    
    # Azure AI Foundry Project
    AZURE_SUBSCRIPTION_ID: str = ""
    AZURE_RESOURCE_GROUP: str = ""
    AZURE_AI_PROJECT_NAME: str = ""
    
    # Azure OpenAI
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_API_KEY: str = ""
    AZURE_OPENAI_DEPLOYMENT: str = "gpt-4"
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT: str = "text-embedding-ada-002"
    AZURE_OPENAI_API_VERSION: str = "2024-02-01"
    
    # Azure AI Search
    AZURE_SEARCH_ENDPOINT: str = ""
    AZURE_SEARCH_KEY: str = ""
    AZURE_SEARCH_INDEX_NAME: str = "market-research-index"
    
    # Azure Blob Storage
    AZURE_STORAGE_CONNECTION_STRING: str = ""
    AZURE_STORAGE_CONTAINER: str = "uploads"
    AZURE_STORAGE_SAS_TOKEN: str = ""
    
    # Azure Document Intelligence
    AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT: str = ""
    AZURE_DOCUMENT_INTELLIGENCE_KEY: str = ""
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./market_research.db"
    
    # Cosmos DB Gremlin (KAG)
    COSMOS_GREMLIN_ENDPOINT: str = ""
    COSMOS_GREMLIN_PORT: int = 443
    COSMOS_GREMLIN_KEY: str = ""
    COSMOS_GREMLIN_DATABASE: str = "KnowledgeGraph"
    COSMOS_GREMLIN_GRAPH: str = "MarketResearch"
    
    # Azure Databricks
    DATABRICKS_WORKSPACE_URL: str = ""
    DATABRICKS_TOKEN: str = ""
    DATABRICKS_CLUSTER_ID: str = ""
    
    # CORS
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:5173", "http://localhost:3000", "http://localhost:8080", "http://localhost:8081"]
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> Any:
        if isinstance(v, str) and not v.strip().startswith("["):
            return [i.strip() for i in v.split(",")]
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


    @property
    def azure_storage_account_name(self) -> str:
        """Extract account name from connection string"""
        if not self.AZURE_STORAGE_CONNECTION_STRING:
            return ""
        try:
            return [p for p in self.AZURE_STORAGE_CONNECTION_STRING.split(";") if p.startswith("AccountName=")][0].split("=")[1]
        except (IndexError, ValueError):
            return ""

    @property
    def azure_storage_account_key(self) -> str:
        """Extract account key from connection string"""
        if not self.AZURE_STORAGE_CONNECTION_STRING:
            return ""
        try:
            return [p for p in self.AZURE_STORAGE_CONNECTION_STRING.split(";") if p.startswith("AccountKey=")][0].split("=")[1]
        except (IndexError, ValueError):
            return ""


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance"""
    return Settings()


settings = get_settings()
