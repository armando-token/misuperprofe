from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.responses import RedirectResponse
import secrets
from datetime import datetime, timedelta, timezone
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession # Para la dependencia de BD

from app.config import settings
from app.db.session import get_session # Para obtener la sesión de BD asíncrona
from app.crud.crud_external_user_map import get_or_create_external_user_map_entry, update_external_user_map_entry # Nueva importación
from app.crud.crud_profesor import get_or_create_profesor_by_email # Importado
from app.models.role_enums import MisuperprofeRole # Para el rol por defecto

# Almacenamiento en memoria para códigos de autorización (SOLO PARA DESARROLLO)
# En producción, usar Redis o una tabla en la BD.
active_auth_codes = {} # Formato: { "auth_code_str": {"external_user_identifier": ..., "client_id": ..., "expires_at": ..., "used": False, "scopes": ...} }

# En un futuro, esto vendría de la configuración o una base de datos de clientes OAuth
VALID_CLIENT_IDS = {"misuperprofe_gpt_client_id"} 
# Esta URL debería ser la que el GPT está configurado para recibir el código
VALID_REDIRECT_URIS = {"https://chat.openai.com/REDIRECT_URI_PLACEHOLDER"} # ¡IMPORTANTE!: Reemplazar con la real

router = APIRouter()

@router.get("/authorize", summary="OAuth 2.0 Authorization Endpoint")
async def authorize(
    request: Request,
    response_type: str,
    client_id: str,
    redirect_uri: str,
    scope: str | None = None, # e.g., "openid profile email"
    state: str | None = None  # Recomendado para prevenir CSRF
):
    """
    Inicia el flujo de autorización OAuth 2.0.
    Por ahora, solo valida el client_id y redirect_uri.
    En una implementación real:
    1. Validar client_id y redirect_uri.
    2. Autenticar al usuario (si no está ya logueado en Misuperprofe - esto será manejado por el flujo de Team).
    3. Pedir consentimiento al usuario para los scopes solicitados.
    4. Si se aprueba, generar un código de autorización y redirigir a redirect_uri con el código y el state.
    """
    if client_id not in VALID_CLIENT_IDS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid client_id")
    
    if redirect_uri not in VALID_REDIRECT_URIS:
        # Idealmente, no se debería redirigir si redirect_uri es inválido, sino mostrar un error.
        # Pero para el flujo de Action de GPT, es mejor intentar la redirección si es posible.
        # OpenAI recomienda devolver el error en la URL de redirección si es inválida.
        # Por ahora, levantamos una excepción.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid redirect_uri")

    if response_type != "code":
        # Podríamos pasar el error a redirect_uri si es válido
        # error_uri = f"{redirect_uri}?error=unsupported_response_type"
        # if state: error_uri += f"&state={state}"
        # return RedirectResponse(url=error_uri, status_code=status.HTTP_302_FOUND)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported response_type")

    # Simulación: El usuario se autentica y Misuperprofe obtiene su ID de Team.
    # En un flujo real, esto sería parte de la autenticación de Misuperprofe o un paso previo.
    simulated_external_user_identifier = "user_from_team@example.com" # Placeholder

    auth_code = f"auth_code_{secrets.token_urlsafe(16)}"
    active_auth_codes[auth_code] = {
        "external_user_identifier": simulated_external_user_identifier,
        "client_id": client_id,
        "redirect_uri": redirect_uri, # Guardar para validación en /token
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=5), # Caducidad corta para el código
        "used": False,
        "scopes": scope.split(" ") if scope else []
    }
    
    redirect_url_parts = [f"{redirect_uri}?code={auth_code}"]
    if state:
        redirect_url_parts.append(f"&state={state}")
    final_redirect_url = "".join(redirect_url_parts)
    return RedirectResponse(url=final_redirect_url, status_code=status.HTTP_302_FOUND)


@router.post("/token", summary="OAuth 2.0 Token Endpoint")
async def token(
    db: AsyncSession = Depends(get_session), # Dependencia de BD añadida
    grant_type: str = Form(...),
    code: str = Form(None), # Puede ser None para otros grant_types
    redirect_uri: str = Form(None), # Requerido para authorization_code
    client_id: str = Form(...),
    client_secret: str = Form(None) # El GPT Action usa "Client authentication: None" o "Basic"
                                    # Si es "None", el client_id se envía en el body.
                                    # Si es "Basic", client_id y client_secret van en Authorization header.
                                    # OpenAI sugiere que el secreto del cliente debe ser manejable.
):
    """
    Intercambia un código de autorización por un token de acceso.
    Por ahora, solo valida el client_id y el grant_type.
    En una implementación real:
    1. Validar client_id (y client_secret si aplica).
    2. Validar grant_type.
    3. Si grant_type es "authorization_code":
        a. Validar el código de autorización (que exista, no haya expirado, no se haya usado, coincida con client_id y redirect_uri).
        b. Invalidar el código de autorización.
        c. Generar un token de acceso JWT (y opcionalmente un refresh token).
    """
    if client_id not in VALID_CLIENT_IDS:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid client_id or client_secret")

    # Aquí, si el client_secret fuera requerido y enviado en el body, se validaría.
    # Si la autenticación del cliente es "Basic", se obtendría del header Authorization.
    # Por ahora, lo mantenemos simple.

    if grant_type == "authorization_code":
        if not code or not redirect_uri:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing code or redirect_uri")

        auth_code_data = active_auth_codes.get(code)

        if not auth_code_data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid authorization code: not found")
        
        if auth_code_data["used"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid authorization code: already used")
        
        if auth_code_data["expires_at"] < datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid authorization code: expired")
            
        if auth_code_data["client_id"] != client_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid authorization code: client_id mismatch")

        if auth_code_data["redirect_uri"] != redirect_uri:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid authorization code: redirect_uri mismatch")

        # Marcar código como usado
        active_auth_codes[code]["used"] = True
        
        retrieved_external_user_identifier = auth_code_data["external_user_identifier"]
        
        # 1. Obtener o crear la entrada del mapa de usuarios
        db_external_user_map_entry = await get_or_create_external_user_map_entry(
            db,
            external_user_identifier=retrieved_external_user_identifier,
            # El rol por defecto aquí se usará si Supabase no devuelve uno o si es la primera vez.
            # Sin embargo, el rol de Supabase tendrá precedencia.
            default_role=MisuperprofeRole.ALUMNO 
        )

        # 2. Obtener el rol real del usuario desde Supabase (actualmente simulado en el CRUD)
        role_from_supabase = get_user_misuperprofe_role_from_supabase(retrieved_external_user_identifier)
        
        # Determinar el rol final. Si Supabase no devuelve un rol, usamos el que ya tiene
        # el usuario en external_user_map (que podría ser el default_role si es nuevo)
        # o lo actualizamos con el de Supabase si es diferente.
        final_misuperprofe_role = role_from_supabase if role_from_supabase is not None else db_external_user_map_entry.assigned_misuperprofe_role
        
        # Si Supabase devolvió un rol y es diferente al que tenemos, o si no había rol y Supabase sí dio uno (aunque sea ALUMNO por defecto desde Supabase)
        if role_from_supabase is not None and db_external_user_map_entry.assigned_misuperprofe_role != role_from_supabase:
            db_external_user_map_entry = await update_external_user_map_entry(
                db,
                db_obj=db_external_user_map_entry,
                assigned_role=role_from_supabase # Usamos el rol de Supabase
            )
            final_misuperprofe_role = role_from_supabase # Nos aseguramos que el rol final es el de Supabase
        elif role_from_supabase is None:
            # Si Supabase no devolvió nada, nos aseguramos de que final_misuperprofe_role sea el que está en la BD
            # que sería el default_role (ALUMNO) si el usuario es completamente nuevo y Supabase no dio info.
            # O el rol que ya tuviera asignado si es un usuario existente y Supabase no respondió.
            # Si db_external_user_map_entry.assigned_misuperprofe_role es None (no debería ocurrir con get_or_create), 
            # entonces podríamos asignar ALUMNO aquí como último recurso.
            final_misuperprofe_role = db_external_user_map_entry.assigned_misuperprofe_role or MisuperprofeRole.ALUMNO


        # 3. (Anterior paso 4) Si el rol final es PROFESOR, asegurar que exista en la tabla Profesor
        if final_misuperprofe_role == MisuperprofeRole.PROFESOR:
            # Nombre y apellido podrían venir de Supabase también en un futuro
            await get_or_create_profesor_by_email(
                db,
                email=retrieved_external_user_identifier,
                nombre_placeholder="Profesor", # Placeholder
                apellido_placeholder="Team"     # Placeholder
            )
        
        if not db_external_user_map_entry.internal_user_id_hash:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to provision internal user identifier")

        # 5. Generar JWT con el rol actualizado
        to_encode = {
            "sub": db_external_user_map_entry.internal_user_id_hash, 
            "external_user_identifier": db_external_user_map_entry.external_user_identifier,
            "role": final_misuperprofe_role.value, # Usar rol final determinado
            "iss": "MisuperprofeOAuthProvider", 
            "aud": client_id, 
            "scope": " ".join(auth_code_data.get("scopes", []))
        }
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_OAUTH_ACCESS_TOKEN_EXPIRE_MINUTES)
        current_time_utc = datetime.now(timezone.utc)
        to_encode.update({"exp": expire.timestamp(), "iat": current_time_utc.timestamp()})
        
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.JWT_OAUTH_SECRET_KEY, 
            algorithm=settings.JWT_OAUTH_ALGORITHM
        )
        
        return {
            "access_token": encoded_jwt,
            "token_type": "Bearer",
            "expires_in": settings.JWT_OAUTH_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "scope": " ".join(auth_code_data.get("scopes", []))
        }
    
    elif grant_type == "refresh_token":
        # Lógica para refresh token (si se implementa)
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Refresh token not implemented")
    
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported grant_type")

# Podríamos añadir más endpoints, como uno para JWKS (JSON Web Key Set) si los tokens son firmados asimétricamente.
# O un endpoint de introspección de tokens. 