from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.api.dependencies.database import get_db
from app.infrastructure.database.models.provider import ProviderModel
from app.schemas.provider import ProviderCreateRequest, ProviderResponse
import uuid

router = APIRouter(prefix="/admin/providers", tags=["Admin - Providers"])

@router.post("/", response_model=ProviderResponse)
async def create_provider(request: ProviderCreateRequest, db: AsyncSession = Depends(get_db)):
    # Check existing
    result = await db.execute(select(ProviderModel).where(ProviderModel.name == request.name))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Provider already exists")
        
    model = ProviderModel(
        id=uuid.uuid4(),
        name=request.name.lower(),
        base_url=request.base_url,
        priority=request.priority
    )
    db.add(model)
    await db.commit()
    return model

@router.get("/", response_model=list[ProviderResponse])
async def list_providers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ProviderModel))
    models = result.scalars().all()
    return models
