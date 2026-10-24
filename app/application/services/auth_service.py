from app.domain.entities.user import User
from app.domain.interfaces.repositories.user_repository import IUserRepository
from app.security.password import verify_password, get_password_hash
from app.security.jwt import create_access_token
from app.schemas.auth import UserLoginRequest, UserCreateRequest, TokenResponse
from app.core.constants import ROLE_USER
from app.core.exceptions import UnauthorizedException, GatewayException

class AuthService:
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    async def authenticate_user(self, request: UserLoginRequest) -> TokenResponse:
        user = await self.user_repo.get_by_email(request.email.lower())
        if not user or not user.is_active:
            raise UnauthorizedException("Incorrect email or password")

        if not verify_password(request.password, user.hashed_password):
            raise UnauthorizedException("Incorrect email or password")

        access_token = create_access_token(subject=str(user.id))
        return TokenResponse(access_token=access_token)

    async def register_user(self, request: UserCreateRequest) -> User:
        email = request.email.lower()
        existing_user = await self.user_repo.get_by_email(email)
        if existing_user:
            raise GatewayException("Email already registered", status_code=400)

        # Public registration can only ever create regular users; admins are
        # bootstrapped from ADMIN_EMAIL / ADMIN_PASSWORD.
        role_id = await self.user_repo.get_role_id_by_name(ROLE_USER)
        if role_id is None:
            raise GatewayException("Default role is not initialised", status_code=500)

        new_user = User(
            email=email,
            hashed_password=get_password_hash(request.password),
            role_id=role_id,
        )
        return await self.user_repo.create(new_user)
