from fastapi import FastAPI
from app.core.config import settings
from app.core.logger import setup_logger
from app.core.constants import PROJECT_NAME, API_V1_STR
from app.api.v1.auth.router import router as auth_router
from app.middlewares.request_context import RequestContextMiddleware
from app.middlewares.logging import LoggingMiddleware
from app.middlewares.metrics import PrometheusMiddleware
from app.api.v1.admin.metrics_router import router as metrics_router
from app.api.v1.admin.provider_router import router as provider_router

def get_application() -> FastAPI:
    setup_logger(settings.ENVIRONMENT)
    
    app = FastAPI(
        title=PROJECT_NAME,
        openapi_url=f"{API_V1_STR}/openapi.json",
        docs_url=f"{API_V1_STR}/docs",
        redoc_url=f"{API_V1_STR}/redoc",
    )
    
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(PrometheusMiddleware)
    
    @app.get("/health/live", tags=["Health"])
    async def health_live():
        return {"status": "alive"}
        
    @app.get("/health/ready", tags=["Health"])
    async def health_ready():
        return {"status": "ready"}
        
    app.include_router(auth_router, prefix=API_V1_STR)
    app.include_router(metrics_router)
    app.include_router(provider_router, prefix=API_V1_STR)
        
    return app
