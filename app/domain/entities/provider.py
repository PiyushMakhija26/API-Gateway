from .base import DomainEntity

class Provider(DomainEntity):
    name: str
    base_url: str
    is_active: bool = True
    priority: int = 0
