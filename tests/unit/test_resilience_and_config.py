import pytest

from app.core.config.base import BaseConfig
from app.core.config.production import ProductionConfig
from app.core.exceptions import UpstreamProviderException
from app.infrastructure.proxy.circuit_breaker import CircuitBreaker
from app.infrastructure.proxy.retry import RetryManager
from app.middlewares.rate_limiter import RedisTokenBucketRateLimiter


async def test_retry_gives_up_after_max_attempts():
    calls = 0

    async def always_fails():
        nonlocal calls
        calls += 1
        raise UpstreamProviderException("down", status_code=502)

    with pytest.raises(UpstreamProviderException):
        await RetryManager.execute_with_retry(always_fails, 3, 0)
    assert calls == 3


async def test_retry_skips_client_errors():
    calls = 0

    async def bad_request():
        nonlocal calls
        calls += 1
        raise UpstreamProviderException("bad", status_code=400)

    with pytest.raises(UpstreamProviderException):
        await RetryManager.execute_with_retry(bad_request, 3, 0)
    assert calls == 1


async def test_circuit_breaker_opens_and_ignores_client_errors():
    breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=60)

    async def client_error():
        raise UpstreamProviderException("bad", status_code=400)

    async def server_error():
        raise UpstreamProviderException("down", status_code=502)

    for _ in range(5):
        with pytest.raises(UpstreamProviderException):
            await breaker.call(client_error)
    assert breaker.state == "CLOSED"

    for _ in range(2):
        with pytest.raises(UpstreamProviderException):
            await breaker.call(server_error)
    assert breaker.state == "OPEN"


async def test_local_token_bucket():
    limiter = RedisTokenBucketRateLimiter("t", capacity=2, refill_rate=0.0001)
    assert [await limiter.is_allowed("a") for _ in range(3)] == [True, True, False]
    assert await limiter.is_allowed("b") is True


def test_database_url_is_translated_for_asyncpg():
    cfg = BaseConfig(DATABASE_URL="postgres://u:p@ep-1.neon.tech/db?sslmode=require&channel_binding=require")
    assert cfg.SQLALCHEMY_DATABASE_URI == "postgresql+asyncpg://u:p@ep-1.neon.tech/db"
    assert cfg.DATABASE_CONNECT_ARGS == {"ssl": True}


def test_discrete_postgres_settings_still_work():
    cfg = BaseConfig(DATABASE_URL=None, POSTGRES_SERVER="postgres")
    assert cfg.SQLALCHEMY_DATABASE_URI == "postgresql+asyncpg://postgres:postgres@postgres:5432/gateway"
    assert cfg.DATABASE_CONNECT_ARGS == {}


def test_redis_url_wins_over_host():
    assert BaseConfig(REDIS_URL="rediss://x:y@host:6380").REDIS_CONNECTION_URL == "rediss://x:y@host:6380"


def test_production_requires_real_secret():
    with pytest.raises(ValueError):
        ProductionConfig(SECRET_KEY="supersecretkey")
    assert ProductionConfig(ENVIRONMENT="production", SECRET_KEY="x" * 40).ENVIRONMENT == "production"
