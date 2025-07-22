from datetime import datetime
from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Schema base con configuración común."""
    
    model_config = ConfigDict(
        from_attributes=True
    )


class TimestampSchema(BaseSchema):
    """Schema con campos de timestamp."""
    created_at: datetime
    updated_at: datetime 