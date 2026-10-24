from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional
from uuid import UUID
from app.domain.entities.user import User
from app.domain.interfaces.repositories.user_repository import IUserRepository
from app.infrastructure.database.models.user import UserModel, RoleModel

class PostgresUserRepository(IUserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        result = await self.session.execute(select(UserModel).where(UserModel.id == user_id))
        model = result.scalar_one_or_none()
        if model:
            return User.model_validate(model)
        return None

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.session.execute(select(UserModel).where(UserModel.email == email))
        model = result.scalar_one_or_none()
        if model:
            return User.model_validate(model)
        return None

    async def create(self, user: User) -> User:
        model = UserModel(
            id=user.id,
            email=user.email,
            hashed_password=user.hashed_password,
            role_id=user.role_id,
            is_active=user.is_active,
            created_at=user.created_at
        )
        self.session.add(model)
        await self.session.commit()
        return user

    async def get_role_id_by_name(self, name: str) -> Optional[UUID]:
        result = await self.session.execute(select(RoleModel.id).where(RoleModel.name == name))
        return result.scalar_one_or_none()

    async def get_role_name(self, role_id: UUID) -> Optional[str]:
        result = await self.session.execute(select(RoleModel.name).where(RoleModel.id == role_id))
        return result.scalar_one_or_none()
