import time
import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger("gateway")

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        
        logger.info("Request started", method=request.method, url=str(request.url))
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            logger.info(
                "Request completed", 
                status_code=response.status_code, 
                process_time=f"{process_time:.4f}s"
            )
            return response
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                "Request failed", 
                error=str(e), 
                process_time=f"{process_time:.4f}s"
            )
            raise
