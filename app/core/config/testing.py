from .base import BaseConfig

class TestingConfig(BaseConfig):
    ENVIRONMENT: str = "testing"
    POSTGRES_DB: str = "gateway_test"
    REDIS_DB: int = 1
