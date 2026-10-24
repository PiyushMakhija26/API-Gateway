from pydantic import BaseModel, EmailStr, Field

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserCreateRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)  # bcrypt ignores bytes past 72
