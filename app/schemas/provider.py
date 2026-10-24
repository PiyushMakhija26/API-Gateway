from pydantic import AnyHttpUrl, BaseModel, ConfigDict, field_validator
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

    @field_validator("base_url")
    @classmethod
    def _valid_url(cls, v: str) -> str:
        AnyHttpUrl(v)
        return v

class ProviderUpdateRequest(BaseModel):
    base_url: Optional[str] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None

    @field_validator("base_url")
    @classmethod
    def _valid_url(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            AnyHttpUrl(v)
        return v
