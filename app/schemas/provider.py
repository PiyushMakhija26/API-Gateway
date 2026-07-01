from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID

class ProviderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    base_url: str
    is_active: bool
    priority: int

class ProviderCreateRequest(BaseModel):
    name: str
    base_url: str
    priority: int = 0
