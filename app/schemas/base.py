from datetime import datetime
from pydantic import BaseModel


class BaseSchema(BaseModel):
    """Schema base con configuración común."""
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TimestampSchema(BaseSchema):
    """Schema con campos de timestamp."""
    created_at: datetime
    updated_at: datetime 