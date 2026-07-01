from fastapi import Depends
from app.api.dependencies.repositories import get_user_repository
from app.domain.interfaces.repositories.user_repository import IUserRepository
from app.application.services.auth_service import AuthService

def get_auth_service(user_repo: IUserRepository = Depends(get_user_repository)) -> AuthService:
    return AuthService(user_repo)
