from contextlib import asynccontextmanager

import httpx
import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.config import settings
from app.core.logger import setup_logger
from app.core.constants import PROJECT_NAME, API_V1_STR
from app.core.exceptions import GatewayException
from app.api.v1.auth.router import router as auth_router
from app.middlewares.request_context import RequestContextMiddleware
from app.middlewares.logging import LoggingMiddleware
from app.middlewares.metrics import PrometheusMiddleware
from app.api.v1.admin.metrics_router import router as metrics_router
from app.api.v1.admin.provider_router import router as provider_router
from app.api.v1.gateway.router import router as gateway_router
from app.application.bootstrap import bootstrap
from app.infrastructure.database import postgres_client

logger = structlog.get_logger("server")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # One pooled HTTP client for all upstream AI calls.
    app.state.http_client = httpx.AsyncClient()
    try:
        await bootstrap(postgres_client.AsyncSessionLocal)
    except Exception as e:
        # The service can still serve health checks; /health/ready reports the DB problem.
        logger.error("Bootstrap failed (has `alembic upgrade head` been run?)", error=str(e))
    yield
    await app.state.http_client.aclose()


def get_application() -> FastAPI:
    setup_logger(settings.ENVIRONMENT)

    app = FastAPI(
        title=PROJECT_NAME,
        openapi_url=f"{API_V1_STR}/openapi.json",
        docs_url=f"{API_V1_STR}/docs",
        redoc_url=f"{API_V1_STR}/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(PrometheusMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Trace-ID", "X-Gateway-Provider", "X-Gateway-Cache"],
    )

    @app.exception_handler(GatewayException)
    async def gateway_exception_handler(request: Request, exc: GatewayException):
        headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message}, headers=headers)

    @app.get("/", include_in_schema=False)
    async def root():
        return {"service": PROJECT_NAME, "docs": f"{API_V1_STR}/docs", "health": "/health/live"}

    @app.get("/health/live", tags=["Health"])
    async def health_live():
        return {"status": "alive"}

    @app.get("/health/ready", tags=["Health"])
    async def health_ready():
        try:
            async with postgres_client.AsyncSessionLocal() as session:
                await session.execute(text("SELECT 1"))
        except Exception as e:
            logger.error("Readiness check failed", error=str(e))
            return JSONResponse(status_code=503, content={"status": "unavailable", "database": "down"})
        return {"status": "ready"}

    app.include_router(auth_router, prefix=API_V1_STR)
    app.include_router(metrics_router)
    app.include_router(provider_router, prefix=API_V1_STR)
    app.include_router(gateway_router, prefix=API_V1_STR)

    if settings.ENVIRONMENT != "production":
        from app.api.v1.dev.router import router as dev_router
        app.include_router(dev_router)

    return app
