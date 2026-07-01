from pydantic import BaseModel, EmailStr
from uuid import UUID

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserCreateRequest(BaseModel):
    email: EmailStr
    password: str
    role_id: UUID
