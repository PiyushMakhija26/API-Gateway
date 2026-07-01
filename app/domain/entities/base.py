from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID, uuid4
from pydantic import Field

class DomainEntity(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
