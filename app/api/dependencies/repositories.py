from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies.database import get_db
from app.infrastructure.repositories.user_repository import PostgresUserRepository
from app.domain.interfaces.repositories.user_repository import IUserRepository

def get_user_repository(db: AsyncSession = Depends(get_db)) -> IUserRepository:
    return PostgresUserRepository(db)
