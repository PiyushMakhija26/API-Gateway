from uuid import UUID
from .base import DomainEntity

class Route(DomainEntity):
    path_prefix: str
    provider_id: UUID
    require_auth: bool = True
    rate_limit_rpm: int = 60
    timeout_seconds: int = 30
    retry_count: int = 3
    is_active: bool = True
