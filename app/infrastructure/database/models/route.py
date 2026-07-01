from sqlalchemy import Column, String, Boolean, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel

class RouteModel(BaseModel):
    __tablename__ = "routes"

    path_prefix = Column(String, unique=True, nullable=False, index=True)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("providers.id"), nullable=False)
    require_auth = Column(Boolean, default=True, nullable=False)
    rate_limit_rpm = Column(Integer, default=60, nullable=False)
    timeout_seconds = Column(Integer, default=30, nullable=False)
    retry_count = Column(Integer, default=3, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    provider = relationship("ProviderModel")
