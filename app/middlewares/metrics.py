import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter(
    "gateway_requests_total", 
    "Total HTTP requests", 
    ["method", "endpoint", "http_status"]
)

REQUEST_LATENCY = Histogram(
    "gateway_request_latency_seconds",
    "HTTP request latency",
    ["method", "endpoint"]
)

class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        method = request.method
        # Simplify endpoint to avoid cardinality explosion
        endpoint = request.url.path
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            status_code = str(response.status_code)
        except Exception:
            status_code = "500"
            raise
        finally:
            latency = time.time() - start_time
            REQUEST_COUNT.labels(method=method, endpoint=endpoint, http_status=status_code).inc()
            REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(latency)
            
        return response
