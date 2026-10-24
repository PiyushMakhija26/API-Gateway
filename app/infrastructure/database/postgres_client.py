from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    echo=(settings.ENVIRONMENT == "development"),
    future=True,
    # Serverless Postgres (Neon, Supabase) closes idle connections, so test
    # each pooled connection before handing it out.
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args=settings.DATABASE_CONNECT_ARGS,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

async def get_db_session():
    async with AsyncSessionLocal() as session:
        yield session
