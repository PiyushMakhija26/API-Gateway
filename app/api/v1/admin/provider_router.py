from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.dependencies.auth import require_admin
from app.api.dependencies.database import get_db
from app.infrastructure.database.models.provider import ProviderModel
from app.schemas.provider import ProviderCreateRequest, ProviderResponse, ProviderUpdateRequest
import uuid

# Every admin endpoint requires a JWT belonging to a user with the admin role.
router = APIRouter(prefix="/admin/providers", tags=["Admin - Providers"], dependencies=[Depends(require_admin)])

@router.post("/", response_model=ProviderResponse)
async def create_provider(request: ProviderCreateRequest, db: AsyncSession = Depends(get_db)):
    name = request.name.strip().lower()
    result = await db.execute(select(ProviderModel).where(ProviderModel.name == name))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Provider already exists")

    model = ProviderModel(
        id=uuid.uuid4(),
        name=name,
        base_url=request.base_url,
        priority=request.priority
    )
    db.add(model)
    await db.commit()
    return model

@router.get("/", response_model=list[ProviderResponse])
async def list_providers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ProviderModel).order_by(ProviderModel.priority.desc(), ProviderModel.name))
    return result.scalars().all()

@router.patch("/{provider_id}", response_model=ProviderResponse)
async def update_provider(provider_id: UUID, request: ProviderUpdateRequest, db: AsyncSession = Depends(get_db)):
    model = await db.get(ProviderModel, provider_id)
    if not model:
        raise HTTPException(status_code=404, detail="Provider not found")
    for field, value in request.model_dump(exclude_unset=True).items():
        setattr(model, field, value)
    await db.commit()
    return model
