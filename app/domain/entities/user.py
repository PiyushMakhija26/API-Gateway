from pydantic import EmailStr
from uuid import UUID
from typing import Optional
from .base import DomainEntity

class Role(DomainEntity):
    name: str
    description: Optional[str] = None

class User(DomainEntity):
    email: EmailStr
    hashed_password: str
    role_id: UUID
    is_active: bool = True
