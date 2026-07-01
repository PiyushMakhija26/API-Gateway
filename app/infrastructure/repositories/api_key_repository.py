from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, List
from uuid import UUID
from app.domain.entities.api_key import APIKey
from app.domain.interfaces.repositories.api_key_repository import IAPIKeyRepository
from app.infrastructure.database.models.api_key import APIKeyModel

class PostgresAPIKeyRepository(IAPIKeyRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_hash(self, key_hash: str) -> Optional[APIKey]:
        result = await self.session.execute(select(APIKeyModel).where(APIKeyModel.key_hash == key_hash))
        model = result.scalar_one_or_none()
        if model:
            return APIKey.model_validate(model)
        return None

    async def get_by_user_id(self, user_id: UUID) -> List[APIKey]:
        result = await self.session.execute(select(APIKeyModel).where(APIKeyModel.user_id == user_id))
        models = result.scalars().all()
        return [APIKey.model_validate(model) for model in models]

    async def create(self, api_key: APIKey) -> APIKey:
        model = APIKeyModel(
            id=api_key.id,
            user_id=api_key.user_id,
            key_hash=api_key.key_hash,
            name=api_key.name,
            is_active=api_key.is_active,
            expires_at=api_key.expires_at,
            created_at=api_key.created_at
        )
        self.session.add(model)
        await self.session.commit()
        return api_key
