from uuid import UUID
from datetime import datetime
from typing import Optional
from .base import DomainEntity

class APIKey(DomainEntity):
    user_id: UUID
    key_hash: str
    name: str
    is_active: bool = True
    expires_at: Optional[datetime] = None
