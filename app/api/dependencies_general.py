import os
from fastapi import HTTPException, Header, status

# Cargar la API_KEY global. Debería estar definida en el entorno.
# Si no está, las llamadas a los endpoints protegidos fallarán como se espera.
API_KEY = os.getenv("API_KEY", "") 

async def verify_api_key_dependency(
    authorization: str = Header(None, description="Bearer token de la API_KEY global.")
):
    """
    Dependencia de FastAPI para verificar la API_KEY global pasada en la cabecera Authorization.
    Ejemplo: Authorization: Bearer tu_api_key_global
    """
    if not API_KEY:
        # Esto indica un problema de configuración del servidor, la API_KEY no está cargada.
        # No deberíamos llegar aquí en un entorno bien configurado.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API Key no configurada en el servidor."
        )

    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Cabecera de autorización faltante."
        )
    
    parts = authorization.split()

    if parts[0].lower() != "bearer" or len(parts) == 1 or len(parts) > 2:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Formato de cabecera de autorización inválido. Debe ser 'Bearer <token>'."
        )
    
    token = parts[1]
    if token != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="API key inválida o incorrecta."
        )
    # Si todo está bien, la dependencia no devuelve nada y la ejecución continúa.
    return None # Opcionalmente podríamos devolver el API_KEY si fuera necesario en el endpoint. 