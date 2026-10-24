from typing import Dict, List, Literal, Optional
from urllib.parse import urlsplit, parse_qsl, urlencode

from pydantic_settings import BaseSettings, SettingsConfigDict

INSECURE_DEFAULT_SECRET = "supersecretkey"


class BaseConfig(BaseSettings):
    ENVIRONMENT: Literal["development", "production", "testing"] = "development"
    PROJECT_NAME: str = "Enterprise AI API Gateway"
    API_V1_STR: str = "/v1"

    # Database. DATABASE_URL (as injected by Render/Neon/Supabase/Railway) wins
    # over the discrete POSTGRES_* values used by docker-compose.
    DATABASE_URL: Optional[str] = None
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "gateway"

    # Redis. REDIS_URL (e.g. rediss://... from Upstash) wins over host/port.
    # With USE_REDIS=false the gateway falls back to in-process rate limiting
    # and caching, which is fine for a single free instance.
    USE_REDIS: bool = True
    REDIS_URL: Optional[str] = None
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # Security
    SECRET_KEY: str = INSECURE_DEFAULT_SECRET
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Optional bootstrap admin, created on startup if both are set.
    ADMIN_EMAIL: Optional[str] = None
    ADMIN_PASSWORD: Optional[str] = None

    # Comma-separated list of allowed browser origins ("*" allows all).
    CORS_ORIGINS: str = "*"

    # Gateway behaviour
    GATEWAY_RATE_LIMIT_CAPACITY: int = 60
    GATEWAY_RATE_LIMIT_REFILL_PER_SEC: float = 1.0
    GATEWAY_CACHE_TTL_SECONDS: int = 60
    GATEWAY_UPSTREAM_TIMEOUT_SECONDS: int = 30
    GATEWAY_MAX_RETRIES: int = 3
    GATEWAY_RETRY_BASE_DELAY_SECONDS: float = 1.0

    # Upstream provider keys, comma-separated so several can be load balanced.
    OPENAI_API_KEYS: str = ""
    GEMINI_API_KEYS: str = ""
    GROQ_API_KEYS: str = ""
    OLLAMA_API_KEYS: str = ""

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return self._database_url_and_args()[0]

    @property
    def DATABASE_CONNECT_ARGS(self) -> dict:
        return self._database_url_and_args()[1]

    def _database_url_and_args(self) -> tuple[str, dict]:
        if not self.DATABASE_URL:
            uri = (
                f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
            return uri, {}

        parts = urlsplit(self.DATABASE_URL)
        scheme = parts.scheme
        if scheme in ("postgres", "postgresql"):
            scheme = "postgresql+asyncpg"

        # asyncpg does not understand libpq's sslmode/channel_binding query
        # parameters, so translate them into an ssl connect arg.
        query = dict(parse_qsl(parts.query))
        sslmode = query.pop("sslmode", None)
        query.pop("channel_binding", None)
        connect_args: dict = {}
        if sslmode in ("require", "verify-ca", "verify-full"):
            connect_args["ssl"] = True

        uri = f"{scheme}://{parts.netloc}{parts.path}" + (f"?{urlencode(query)}" if query else "")
        return uri, connect_args

    @property
    def REDIS_CONNECTION_URL(self) -> str:
        return self.REDIS_URL or f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def provider_api_keys(self) -> Dict[str, List[str]]:
        raw = {
            "openai": self.OPENAI_API_KEYS,
            "gemini": self.GEMINI_API_KEYS,
            "groq": self.GROQ_API_KEYS,
            "ollama": self.OLLAMA_API_KEYS,
        }
        return {name: [k.strip() for k in value.split(",") if k.strip()] for name, value in raw.items()}

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8', case_sensitive=True, extra="ignore")
