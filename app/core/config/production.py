from .base import BaseConfig

class ProductionConfig(BaseConfig):
    ENVIRONMENT: str = "production"
