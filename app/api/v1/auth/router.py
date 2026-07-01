from fastapi import APIRouter, Depends
from app.schemas.auth import UserLoginRequest, UserCreateRequest, TokenResponse
from app.application.services.auth_service import AuthService
from app.api.dependencies.services import get_auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=TokenResponse)
async def login(
    request: UserLoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    return await auth_service.authenticate_user(request)

@router.post("/register")
async def register(
    request: UserCreateRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    user = await auth_service.register_user(request)
    return {"id": user.id, "email": user.email}
