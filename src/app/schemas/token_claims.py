from pydantic import BaseModel
from typing import Optional

class TokenClaims(BaseModel):
    sub: str  # Identificador interno del usuario en Misuperprofe (user_id_hash)
    external_user_identifier: str  # Identificador del usuario en Team (e.g., email)
    role: str  # Rol asignado en Misuperprofe (alumno, profesor, admin_academia)
    name: Optional[str] = None # Nombre para mostrar del usuario, añadido desde WordPress
    iss: Optional[str] = None # Emisor del token
    aud: Optional[str] = None # Audiencia del token
    exp: Optional[int] = None # Tiempo de expiración (timestamp)
    iat: Optional[int] = None # Tiempo de emisión (timestamp)
    # Puedes añadir otros claims que tu servidor OAuth pueda incluir y sean útiles aquí
    # Por ejemplo, internal_user_id_hash si ya está resuelto y se incluye en el token
    # internal_user_id_hash: Optional[str] = None 