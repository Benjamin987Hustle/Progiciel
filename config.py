"""
Configuration globale du système ERPsim
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Configuration de l'application"""

    # Connexion OData
    ODATA_BASE_URL: str = "https://sapvm2.hec.ca:8001/odata/300"
    ODATA_USERNAME: str = "H_5"
    ODATA_PASSWORD: str = "Canada"

    # Simulation
    COMPANY_CODE: str = "H2"
    PLANT: str = "1000"

    # Options
    CACHE_ENABLED: bool = True
    DEBUG: bool = False
    REFRESH_RATE: int = 30

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Instance globale
settings = Settings()
