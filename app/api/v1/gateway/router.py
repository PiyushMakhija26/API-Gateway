from typing import List

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.database import get_db
from app.application.services.gateway_service import GatewayService
from app.domain.entities.provider import Provider
from app.domain.entities.user import User
from app.infrastructure.database.models.provider import ProviderModel
from app.infrastructure.proxy.proxy_engine import ProxyEngine
from app.infrastructure.proxy.router import GatewayRouter
from app.schemas.gateway import ChatCompletionRequest

router = APIRouter(prefix="/gateway", tags=["Gateway"])


async def get_gateway_service(request: Request, db: AsyncSession = Depends(get_db)) -> GatewayService:
    result = await db.execute(select(ProviderModel))
    providers: List[Provider] = [Provider.model_validate(m) for m in result.scalars().all()]
    engine = ProxyEngine(request.app.state.http_client)
    return GatewayService(GatewayRouter(engine), providers)


@router.post("/chat/completions")
async def chat_completions(
    payload: ChatCompletionRequest,
    response: Response,
    user: User = Depends(get_current_user),
    service: GatewayService = Depends(get_gateway_service),
):
    result, provider_name, cached = await service.chat(user.id, payload.model_dump(exclude_none=True))
    response.headers["X-Gateway-Provider"] = provider_name
    response.headers["X-Gateway-Cache"] = "HIT" if cached else "MISS"
    return result
