from pydantic_settings import BaseSettings, SettingsConfigDict

class GraphSettings(BaseSettings):
    
    AZURE_CLIENT_ID: str
    AZURE_CLIENT_SECRET: str
    AZURE_TENANT_ID: str
    
    EMAIL_ADDRESS: str
    
    DATABASE_URL: str
    
    OPENAI_API_KEY: str
    
    SECRET_KEY: str
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="allow"
    )

graph_settings = GraphSettings() 