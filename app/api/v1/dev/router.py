"""Endpoints for exercising the rate limiter and circuit breaker during load tests.

Only mounted outside production (see server.py)."""
import asyncio

from fastapi import APIRouter, HTTPException

from app.core.exceptions import UpstreamProviderException
from app.infrastructure.proxy.circuit_breaker import CircuitBreaker
from app.middlewares.rate_limiter import RedisTokenBucketRateLimiter

router = APIRouter(tags=["Test"])

test_limiter = RedisTokenBucketRateLimiter("test_endpoint", capacity=100, refill_rate=20)
test_cb = CircuitBreaker(failure_threshold=3, recovery_timeout=15)


@router.get("/unprotected-route")
async def unprotected_route():
    return {"message": "success"}


@router.get("/protected-route")
async def protected_route():
    if not await test_limiter.is_allowed("global"):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    return {"message": "success"}


async def mock_upstream_call():
    await asyncio.sleep(0.5)
    raise UpstreamProviderException("Upstream failed", status_code=502)


@router.get("/route-to-dead-upstream")
async def circuit_breaker_route():
    try:
        await test_cb.call(mock_upstream_call)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    return {"message": "success"}
