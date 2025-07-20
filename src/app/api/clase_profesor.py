from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_session
from app.schemas.clase_schemas import GrupoClaseCreate, GrupoClasePublic, GrupoClaseConDetallesPublic, AlumnoEnClaseInfo
from app.schemas.profesor_schemas import ProfesorPublic
from app.schemas.curso import CursoPublico
from app.schemas.user_status_schemas import AlumnoClaseProgresoResponse, AlumnoProgresoCursoInfo, AlumnoProgresoCapituloInfo, UserChapterStatus
from app.crud import crud_clase, crud_progreso_alumno, crud_user, crud_profesor
from app.models.role_enums import MisuperprofeRole
from app.api.dependencies_team import get_current_team_user_claims
from app.schemas.token_claims import TokenClaims
from app.schemas.progreso_alumno_schemas import ProgresoCursoParaProfesor, ProgresoCapituloParaProfesor, ProgresoAlumnoGlobal

router = APIRouter(prefix="/api/profesor/clases", tags=["clases_profesor"])

@router.post("", response_model=GrupoClasePublic, status_code=status.HTTP_201_CREATED)
async def crear_nueva_clase(
    *, 
    db: AsyncSession = Depends(get_session),
    clase_in: GrupoClaseCreate,
    current_claims: TokenClaims = Depends(get_current_team_user_claims)
):
    """Crea una nueva clase para el profesor autenticado, asociando los cursos especificados."""
    if current_claims.role != MisuperprofeRole.PROFESOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. Se requiere rol de profesor."
        )

    profesor_email = current_claims.external_user_identifier
    if not profesor_email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Identificador externo no encontrado en el token para el profesor."
        )

    current_profesor_db_object = await crud_profesor.get_profesor_by_email(db, email=profesor_email)
    if not current_profesor_db_object:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profesor con email '{profesor_email}' no encontrado en el sistema."
        )
    if not current_profesor_db_object.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Profesor inactivo")
    
    profesor_id_for_crud = current_profesor_db_object.id

    nueva_clase_db = await crud_clase.create_clase(db=db, clase_in=clase_in, profesor_id=profesor_id_for_crud)
    if not nueva_clase_db:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error al crear la clase.")

    cursos_publicos = []
    if nueva_clase_db.cursos:
        for curso_db in nueva_clase_db.cursos:
            cursos_publicos.append(
                CursoPublico.from_orm(curso_db)
            )
    
    return GrupoClasePublic(
        id=nueva_clase_db.id,
        nombre_clase=nueva_clase_db.nombre_clase,
        descripcion=nueva_clase_db.descripcion,
        codigo_clase=nueva_clase_db.codigo_clase,
        created_at=nueva_clase_db.created_at,
        cursos=cursos_publicos
    )

@router.get("", response_model=List[GrupoClasePublic])
async def listar_clases_del_profesor(
    *, 
    db: AsyncSession = Depends(get_session),
    current_claims: TokenClaims = Depends(get_current_team_user_claims),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200)
):
    """Lista las clases creadas por el profesor autenticado, incluyendo los cursos asociados."""
    if current_claims.role != MisuperprofeRole.PROFESOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. Se requiere rol de profesor."
        )

    profesor_email = current_claims.external_user_identifier
    if not profesor_email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Identificador externo no encontrado en el token para el profesor."
        )

    current_profesor_db_object = await crud_profesor.get_profesor_by_email(db, email=profesor_email)
    if not current_profesor_db_object:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profesor con email '{profesor_email}' no encontrado en el sistema."
        )
    if not current_profesor_db_object.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Profesor inactivo")
        
    profesor_id_for_crud = current_profesor_db_object.id
    
    clases_db = await crud_clase.get_clases_by_profesor(db=db, profesor_id=profesor_id_for_crud, skip=skip, limit=limit)
    
    clases_publicas = []
    for clase_db in clases_db:
        cursos_publicos = [CursoPublico.from_orm(c) for c in clase_db.cursos] if clase_db.cursos else []
        clases_publicas.append(
            GrupoClasePublic(
                id=clase_db.id,
                nombre_clase=clase_db.nombre_clase,
                descripcion=clase_db.descripcion,
                codigo_clase=clase_db.codigo_clase,
                created_at=clase_db.created_at,
                cursos=cursos_publicos
            )
        )
    return clases_publicas

@router.get("/{clase_id}", response_model=GrupoClaseConDetallesPublic)
async def obtener_detalles_de_clase(
    *, 
    db: AsyncSession = Depends(get_session),
    clase_id: int,
    current_claims: TokenClaims = Depends(get_current_team_user_claims)
):
    """
    Obtiene los detalles de una clase específica, incluyendo profesores, alumnos y cursos asociados.
    La dependencia verify_profesor_clase_access ya asegura que el profesor solicitante:
    1. Tenga rol PROFESOR.
    2. Tenga un external_user_identifier.
    3. Esté asociado a la clase (verificación vía Supabase).
    """
    clase_obj = await crud_clase.get_clase_by_id(db=db, clase_id=clase_id)
    if not clase_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clase no encontrada")
    
    profesores_public = [ProfesorPublic.from_orm(p) for p in clase_obj.profesores]
    alumnos_info = [
        AlumnoEnClaseInfo(
            user_id_hash=assoc.user_id_hash,
            fecha_inscripcion=assoc.fecha_inscripcion
        )
        for assoc in clase_obj.alumnos_association
    ]
    cursos_publicos = [CursoPublico.from_orm(c) for c in clase_obj.cursos] if clase_obj.cursos else []

    return GrupoClaseConDetallesPublic(
        id=clase_obj.id,
        nombre_clase=clase_obj.nombre_clase,
        descripcion=clase_obj.descripcion,
        codigo_clase=clase_obj.codigo_clase,
        created_at=clase_obj.created_at,
        profesores=profesores_public,
        alumnos=alumnos_info,
        cursos=cursos_publicos
    )

@router.get("/{clase_id}/alumnos/{user_id_hash}/progreso", response_model=List[ProgresoCursoParaProfesor])
async def obtener_progreso_alumno_en_clase(
    *, 
    db: AsyncSession = Depends(get_session),
    clase_id: int = Path(..., description="ID de la clase"),
    user_id_hash: str = Path(..., description="ID hash del alumno"),
    current_claims: TokenClaims = Depends(get_current_team_user_claims)
):
    """
    Obtiene el progreso de un alumno específico dentro de los cursos asociados a una clase.
    La dependencia verify_profesor_clase_access ya asegura que el profesor solicitante:
    1. Tenga rol PROFESOR.
    2. Tenga un external_user_identifier.
    3. Esté asociado a la clase (verificación vía Supabase).
    """
    clase_obj = await crud_clase.get_clase_by_id(db=db, clase_id=clase_id)
    if not clase_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Clase con ID {clase_id} no encontrada.")

    # Verificar si el alumno pertenece a la clase (lógica local actual)
    # TODO: Esta verificación también podría moverse o ser complementada por Supabase en el futuro,
    # por ejemplo, para obtener directamente la lista de alumnos de una clase gestionada en Supabase.
    # Por ahora, se asume que la pertenencia del alumno a la clase se sigue gestionando en Misuperprofe DB.
    alumno_en_clase = await crud_clase.get_alumno_in_clase(db=db, clase_id=clase_id, user_id_hash=user_id_hash)
    if not alumno_en_clase:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Alumno con ID hash {user_id_hash} no encontrado en la clase ID {clase_id}.")

    # Obtener los IDs de los cursos asociados a esta clase
    curso_ids_en_clase = [curso.id for curso in clase_obj.cursos]
    if not curso_ids_en_clase:
        return [] # No hay cursos en la clase, por lo tanto, no hay progreso que mostrar.

    # Obtener el progreso del alumno para esos cursos
    progreso_cursos_db = await crud_progreso_alumno.get_progreso_alumno_por_cursos(
        db=db, 
        user_id_hash=user_id_hash, 
        curso_ids=curso_ids_en_clase
    )
    return progreso_cursos_db 