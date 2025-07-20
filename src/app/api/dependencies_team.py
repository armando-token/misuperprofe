from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError

from app.config import settings
from app.schemas.token_claims import TokenClaims

# Esta URL "tokenUrl" es un placeholder. En un flujo OAuth 2.0 completo,
# el cliente obtendría el token de un endpoint de token real del servidor OAuth.
# Para la validación de un token ya emitido, esta URL no se usa directamente por esta dependencia,
# pero OAuth2PasswordBearer la requiere.
reusable_oauth2_team = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/team/placeholder_token_url"
)

async def get_current_team_user_claims(token: str = Depends(reusable_oauth2_team)) -> TokenClaims:
    print(">>> [AUTH_DEBUG] Attempting to get current team user claims.")
    print(f">>> [AUTH_DEBUG] Token received: {token}")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials from Team JWT",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        print(">>> [AUTH_DEBUG] Attempting jwt.decode...")
        payload = jwt.decode(
            token,
            settings.JWT_OAUTH_SECRET_KEY, 
            algorithms=[settings.JWT_OAUTH_ALGORITHM],
            audience='https://app.misuperprofe.com',
            # Podríamos añadir validación de audiencia (aud) y emisor (iss) aquí si es necesario
            # options={"verify_aud": True, "verify_iss": True}, # Requeriría pasar los valores esperados
        )
        print(f">>> [AUTH_DEBUG] jwt.decode successful. Payload: {payload}")
        
        # Validar el payload completo con el esquema Pydantic TokenClaims
        # Esto asegura que todos los campos requeridos (sub, external_user_identifier, role)
        # están presentes y que los opcionales (iss, aud, exp, iat) son del tipo correcto si existen.
        print(">>> [AUTH_DEBUG] Attempting TokenClaims(**payload) validation...")
        token_data = TokenClaims(**payload) # Desempaquetar el payload en el modelo
        print(f">>> [AUTH_DEBUG] TokenClaims validation successful. Token_data: {token_data.model_dump_json(indent=2)}")

    except (JWTError, ValidationError) as e:
        print(f">>> [AUTH_DEBUG] JWT validation/decoding error inside try-except: {e}")
        raise credentials_exception
    
    # Verificar manualmente si los campos esenciales están realmente allí, aunque Pydantic lo hace.
    if not token_data.sub or not token_data.external_user_identifier or not token_data.role:
        # print("Essential claims missing after Pydantic validation") # Debug
        print(">>> [AUTH_DEBUG] Essential claims missing after Pydantic validation (sub, external_user_identifier, or role).")
        raise credentials_exception
        
    print(f">>> [AUTH_DEBUG] All checks passed. Returning token_data: {token_data.model_dump_json(indent=2)}")
    return token_data

# Podríamos añadir otra dependencia que, usando get_current_team_user_claims,
# también busque el usuario en la base de datos (ExternalUserMap y UserProgress)
# y devuelva el objeto del modelo, pero por ahora nos centramos en validar el token y los claims.
