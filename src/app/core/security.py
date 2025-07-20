from datetime import datetime, timedelta, timezone
from typing import Optional, Union, Any

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.config import settings # Corregir la ruta de importación de settings

# Configuración de Passlib para el hashing de contraseñas
# Usamos bcrypt como el esquema principal
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = settings.ALGORITHM
SECRET_KEY = settings.SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica una contraseña plana contra una hasheada."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Genera el hash de una contraseña."""
    return pwd_context.hash(password)

def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None, is_profesor: bool = False) -> str:
    """Crea un nuevo token de acceso JWT."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject), "is_profesor": is_profesor}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Podríamos añadir una función para decodificar tokens si fuera necesario aquí,
# pero a menudo la dependencia de FastAPI (OAuth2PasswordBearer) maneja esto.
# def decode_token(token: str) -> Optional[dict]:
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         return payload
#     except JWTError:
#         return None 