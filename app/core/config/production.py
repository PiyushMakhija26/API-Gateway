from pydantic import model_validator

from .base import BaseConfig, INSECURE_DEFAULT_SECRET


class ProductionConfig(BaseConfig):
    ENVIRONMENT: str = "production"

    @model_validator(mode="after")
    def _require_real_secret(self):
        if self.SECRET_KEY == INSECURE_DEFAULT_SECRET or len(self.SECRET_KEY) < 32:
            raise ValueError("SECRET_KEY must be set to a random value of at least 32 characters in production")
        return self
