from sqlalchemy import Column, String, Boolean, Integer
from .base import BaseModel

class ProviderModel(BaseModel):
    __tablename__ = "providers"

    name = Column(String, unique=True, nullable=False)
    base_url = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    priority = Column(Integer, default=0, nullable=False)
