from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional

class ProfesorBase(BaseModel):
    email: EmailStr
    nombre: str = Field(..., min_length=1, max_length=100)
    apellido: str = Field(..., min_length=1, max_length=100)

class ProfesorCreate(ProfesorBase):
    password: str = Field(..., min_length=8)

class ProfesorLogin(BaseModel):
    email: EmailStr
    password: str

class ProfesorPublic(ProfesorBase):
    id: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[EmailStr] = None
    is_profesor: bool = False # Para diferenciar de tokens de usuario alumno si fuera necesario 