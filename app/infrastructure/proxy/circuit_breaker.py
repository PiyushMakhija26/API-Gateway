import time
from typing import Callable, Any
import structlog
from app.core.exceptions import UpstreamProviderException

logger = structlog.get_logger("circuit_breaker")

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "CLOSED" # CLOSED, OPEN, HALF_OPEN
        
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        current_time = time.time()
        
        if self.state == "OPEN":
            if current_time - self.last_failure_time >= self.recovery_timeout:
                self.state = "HALF_OPEN"
                logger.info("Circuit breaker entering HALF_OPEN state")
            else:
                raise UpstreamProviderException("Circuit Breaker is OPEN. Provider temporarily unavailable.", status_code=503)
                
        try:
            result = await func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self._reset()
            return result
        except Exception as e:
            self._record_failure()
            raise e
            
    def _record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning("Circuit breaker transitioning to OPEN state due to failures")
            
    def _reset(self):
        self.state = "CLOSED"
        self.failure_count = 0
        logger.info("Circuit breaker transitioning to CLOSED state (Healthy)")
