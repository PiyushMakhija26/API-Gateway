from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID
from app.domain.entities.api_key import APIKey

class IAPIKeyRepository(ABC):
    @abstractmethod
    async def get_by_hash(self, key_hash: str) -> Optional[APIKey]:
        pass
        
    @abstractmethod
    async def get_by_user_id(self, user_id: UUID) -> List[APIKey]:
        pass

    @abstractmethod
    async def create(self, api_key: APIKey) -> APIKey:
        pass
