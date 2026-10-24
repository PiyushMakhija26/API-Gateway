from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.dependencies.repositories import get_user_repository
from app.core.constants import ROLE_ADMIN
from app.core.exceptions import UnauthorizedException, ForbiddenException
from app.domain.entities.user import User
from app.domain.interfaces.repositories.user_repository import IUserRepository
from app.security.jwt import decode_access_token
from uuid import UUID

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    user_repo: IUserRepository = Depends(get_user_repository),
) -> User:
    if credentials is None:
        raise UnauthorizedException("Missing bearer token")
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = UUID(payload["sub"])
    except (ValueError, KeyError):
        raise UnauthorizedException("Invalid or expired token")

    user = await user_repo.get_by_id(user_id)
    if not user or not user.is_active:
        raise UnauthorizedException("User not found or inactive")
    return user


async def require_admin(
    user: User = Depends(get_current_user),
    user_repo: IUserRepository = Depends(get_user_repository),
) -> User:
    if await user_repo.get_role_name(user.role_id) != ROLE_ADMIN:
        raise ForbiddenException("Admin privileges required")
    return user
