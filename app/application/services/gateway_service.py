from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import structlog

from app.core.config import settings
from app.core.exceptions import (
    GatewayException, NotFoundException, RateLimitExceededException, UpstreamProviderException,
)
from app.domain.entities.provider import Provider
from app.domain.entities.route import Route
from app.infrastructure.proxy.cache_manager import CacheManager
from app.infrastructure.proxy.circuit_breaker import CircuitBreaker
from app.infrastructure.proxy.retry import RetryManager
from app.infrastructure.proxy.router import GatewayRouter
from app.middlewares.rate_limiter import RedisTokenBucketRateLimiter

logger = structlog.get_logger("gateway_service")

CHAT_PATH = "/chat/completions"

# Process-wide state: one breaker per provider, one limiter for all callers.
_breakers: Dict[str, CircuitBreaker] = {}
_limiter = RedisTokenBucketRateLimiter(
    "gateway", settings.GATEWAY_RATE_LIMIT_CAPACITY, settings.GATEWAY_RATE_LIMIT_REFILL_PER_SEC
)


def get_breaker(provider_name: str) -> CircuitBreaker:
    if provider_name not in _breakers:
        _breakers[provider_name] = CircuitBreaker(failure_threshold=5, recovery_timeout=30)
    return _breakers[provider_name]


class GatewayService:
    def __init__(self, router: GatewayRouter, providers: List[Provider]):
        self.router = router
        self.providers = providers

    async def chat(self, user_id: UUID, body: Dict[str, Any]) -> Tuple[Dict[str, Any], str, bool]:
        """Returns (response, provider_name, served_from_cache)."""
        if body.get("stream"):
            raise GatewayException("Streaming responses are not supported by this gateway", status_code=400)
        body = {k: v for k, v in body.items() if k != "stream"}

        if not await _limiter.is_allowed(str(user_id)):
            raise RateLimitExceededException()

        requested = body.pop("provider", None)
        candidates = self._candidates(requested)

        last_error: Optional[Exception] = None
        for provider in candidates:
            cache_path = f"{provider.name}{CHAT_PATH}"
            cached = await CacheManager.get_cached_response(cache_path, body)
            if cached is not None:
                return cached, provider.name, True

            try:
                response = await self._call_provider(provider, body)
            except UpstreamProviderException as e:
                last_error = e
                logger.warning("Provider failed", provider=provider.name, error=str(e))
                # A bad request is the caller's problem; another provider will not help.
                if 400 <= e.status_code < 500 and e.status_code != 429:
                    raise
                continue

            await CacheManager.set_cached_response(cache_path, body, response, settings.GATEWAY_CACHE_TTL_SECONDS)
            return response, provider.name, False

        assert last_error is not None
        raise last_error

    def _candidates(self, requested: Optional[str]) -> List[Provider]:
        keys = settings.provider_api_keys
        active = sorted((p for p in self.providers if p.is_active), key=lambda p: p.priority, reverse=True)

        if requested:
            match = [p for p in active if p.name == requested.lower()]
            if not match:
                raise NotFoundException(f"Provider '{requested}' not found or inactive")
            if not keys.get(match[0].name) and match[0].name != "ollama":
                raise GatewayException(f"No API key configured for provider '{requested}'", status_code=503)
            return match

        usable = [p for p in active if keys.get(p.name) or p.name == "ollama"]
        if not usable:
            raise GatewayException("No providers are configured with an API key", status_code=503)
        return usable

    async def _call_provider(self, provider: Provider, body: Dict[str, Any]) -> Dict[str, Any]:
        route = Route(
            path_prefix=CHAT_PATH,
            provider_id=provider.id,
            timeout_seconds=settings.GATEWAY_UPSTREAM_TIMEOUT_SECONDS,
            retry_count=settings.GATEWAY_MAX_RETRIES,
        )
        api_keys = settings.provider_api_keys.get(provider.name, [])

        async def attempt() -> Dict[str, Any]:
            return await self.router.route_request(route, provider, api_keys, body)

        # The breaker wraps the retries so one failed request counts once.
        return await get_breaker(provider.name).call(
            RetryManager.execute_with_retry, attempt, route.retry_count, settings.GATEWAY_RETRY_BASE_DELAY_SECONDS
        )
