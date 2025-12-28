from pydantic import BaseModel, ConfigDict
from typing import List, Optional

class ServiceSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str = ""
    icon: str = "fas fa-tools"

class CategoryMappingSchema(BaseModel):
    """Schema for category -> list of services mapping used in frontend"""
    services: List[ServiceSchema]
