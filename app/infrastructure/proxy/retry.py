import asyncio
from typing import Callable, Any
import structlog
from app.core.exceptions import UpstreamProviderException

logger = structlog.get_logger("retry_manager")

class RetryManager:
    @staticmethod
    async def execute_with_retry(func: Callable, max_retries: int = 3, base_delay: float = 1.0, *args, **kwargs) -> Any:
        attempts = 0
        while attempts < max_retries:
            try:
                return await func(*args, **kwargs)
            except UpstreamProviderException as e:
                attempts += 1
                if attempts >= max_retries:
                    logger.error("Max retries exhausted", attempts=attempts, error=str(e))
                    raise
                
                delay = base_delay * (2 ** (attempts - 1)) # Exponential backoff
                logger.warning(f"Retry attempt {attempts}/{max_retries} failed. Retrying in {delay}s...")
                await asyncio.sleep(delay)
