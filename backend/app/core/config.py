from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    OPENROUTER_API_KEY: str
    OPENROUTER_MODEL: str
    GROQ_API_KEY: str
    GROQ_MODEL: str
    ESP32_IP: str
    HA_URL: Optional[str] = "http://192.168.100.150:8123"
    HA_TOKEN: Optional[str] = None

    class Config:
        env_file = ".env"

settings = Settings()
