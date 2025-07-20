from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.schemas.clase_schemas import AlumnoUnirseClaseRequest, GrupoClasePublicConAlumnos
from app.crud import crud_clase, crud_user
import logging

from app.api.dependencies_team import get_current_team_user_claims
from app.schemas.token_claims import TokenClaims

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/clases",
    tags=["clases_alumnos"]
)

@router.post("/join", response_model=GrupoClasePublicConAlumnos, status_code=status.HTTP_200_OK)
async def alumno_unirse_a_clase(
    request_data: AlumnoUnirseClaseRequest,
    db: AsyncSession = Depends(get_session),
    current_claims: TokenClaims = Depends(get_current_team_user_claims)
):
    user_id_hash_from_token = current_claims.sub
    external_user_identifier_from_token = current_claims.external_user_identifier

    logger.info(f"Endpoint alumno_unirse_a_clase: user_hash={user_id_hash_from_token}, external_id={external_user_identifier_from_token}, codigo_clase={request_data.codigo_clase}")

    if not external_user_identifier_from_token:
        logger.warning("No se encontró external_user_identifier en el token.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Identificador externo no encontrado en el token.")

    try:
        # 1. Buscar la clase por código en la base de datos local
        clase_local = await crud_clase.get_clase_by_codigo(db, codigo_clase=request_data.codigo_clase)
        if not clase_local:
            logger.warning(f"Clase con código '{request_data.codigo_clase}' no encontrada en la base de datos local.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clase no encontrada o no disponible para unirse.")

        # 2. Verificar que el usuario local (UserProgress) exista
        user_progress_record = await crud_user.get_user_by_hash(db, user_id_hash=user_id_hash_from_token)
        if not user_progress_record:
            logger.warning(f"Usuario autenticado {user_id_hash_from_token} (external: {external_user_identifier_from_token}) no encontrado en la DB local UserProgress.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario autenticado no encontrado en el sistema Misuperprofe.")

        # 3. Verificar si el alumno ya está inscrito en la clase localmente
        alumno_en_clase = await crud_clase.get_alumno_in_clase(db, clase_id=clase_local.id, user_id_hash=user_id_hash_from_token)
        if alumno_en_clase:
            logger.info(f"Alumno '{user_id_hash_from_token}' ya está inscrito en la clase localmente.")
            return clase_local

        # 4. Inscribir al alumno en la clase localmente
        association_local = await crud_clase.add_alumno_a_clase(
            db,
            clase_id=clase_local.id,
            user_id_hash=user_id_hash_from_token
        )
        if not association_local:
            logger.error(f"Falló la creación de la asociación local para alumno '{user_id_hash_from_token}' en clase ID {clase_local.id}.")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al inscribir al alumno en la clase.")

        logger.info(f"Alumno '{user_id_hash_from_token}' inscrito localmente en clase ID {clase_local.id}. Recargando detalles.")
        clase_actualizada = await crud_clase.get_clase_by_id(db, clase_id=clase_local.id)
        if not clase_actualizada:
            logger.error(f"Clase ID {clase_local.id} no encontrada en DB local después de inscripción (inesperado).")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al obtener la clase después de la inscripción.")

        return clase_actualizada

    except HTTPException as http_exc:
        logger.info(f"Propagando HTTPException: {http_exc.status_code} - {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error(f"Excepción no controlada en alumno_unirse_a_clase: {type(e).__name__} - {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error interno del servidor al unirse a la clase: {type(e).__name__}") 