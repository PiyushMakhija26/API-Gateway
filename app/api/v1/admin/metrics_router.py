from fastapi import APIRouter
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

router = APIRouter(prefix="/admin/metrics", tags=["Metrics"])

@router.get("/")
async def get_metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
