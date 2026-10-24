"""Idempotent first-run data: roles, default providers, optional admin user."""
import structlog
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.future import select

from app.core.config import settings
from app.core.constants import ROLE_ADMIN, ROLE_USER
from app.infrastructure.database.models.provider import ProviderModel
from app.infrastructure.database.models.user import RoleModel, UserModel
from app.security.password import get_password_hash

logger = structlog.get_logger("bootstrap")

# (name, chat-completions URL, priority, active). All four expose an
# OpenAI-compatible chat endpoint, which is what the adapters pass through.
DEFAULT_PROVIDERS = [
    ("openai", "https://api.openai.com/v1/chat/completions", 10, True),
    ("groq", "https://api.groq.com/openai/v1/chat/completions", 20, True),
    ("gemini", "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions", 15, True),
    # Ollama is local-only, so it stays off until an operator points it at a reachable host.
    ("ollama", "http://localhost:11434/v1/chat/completions", 0, False),
]


async def bootstrap(session_factory: async_sessionmaker) -> None:
    async with session_factory() as session:
        roles = {}
        for name in (ROLE_ADMIN, ROLE_USER):
            role = (await session.execute(select(RoleModel).where(RoleModel.name == name))).scalar_one_or_none()
            if role is None:
                role = RoleModel(name=name, description=f"{name} role")
                session.add(role)
            roles[name] = role

        for name, url, priority, active in DEFAULT_PROVIDERS:
            exists = (await session.execute(select(ProviderModel).where(ProviderModel.name == name))).scalar_one_or_none()
            if exists is None:
                session.add(ProviderModel(name=name, base_url=url, priority=priority, is_active=active))

        await session.flush()

        if settings.ADMIN_EMAIL and settings.ADMIN_PASSWORD:
            email = settings.ADMIN_EMAIL.lower()
            admin = (await session.execute(select(UserModel).where(UserModel.email == email))).scalar_one_or_none()
            if admin is None:
                session.add(UserModel(
                    email=email,
                    hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
                    role_id=roles[ROLE_ADMIN].id,
                ))
                logger.info("Created bootstrap admin user", email=email)

        await session.commit()
