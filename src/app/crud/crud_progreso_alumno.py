from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import aliased, joinedload, selectinload

from app.models.adaptive import UserProgress, ProgressUnit, SpacedRepetition, UserChapterStatus
from app.models.curso import Curso
from app.models.capitulo import Capitulo
from app.schemas.progreso_alumno_schemas import ProgresoCursoParaProfesor, ProgresoCapituloParaProfesor, ProgresoAlumnoGlobal


async def get_progreso_alumno_por_cursos(
    db: AsyncSession, 
    user_id_hash: str, 
    ids_cursos_de_clase: list[int]
) -> list[ProgresoCursoParaProfesor]:
    """
    Obtiene el progreso de un alumno específico en una lista de cursos determinados (los de la clase).
    Para cada curso, lista los capítulos con su estado y porcentaje de progreso.
    """
    cursos_progreso = []
    for curso_id in ids_cursos_de_clase:
        curso_stmt = (
            select(Curso)
            .options(selectinload(Curso.capitulos).selectinload(Capitulo.progress_units))
            .where(Curso.id == curso_id)
        )
        curso_obj = (await db.execute(curso_stmt)).scalars().first()
        if not curso_obj:
            continue
        
        capitulos_data = []
        for cap in curso_obj.capitulos:
            progreso_capitulo_especifico = None
            # Buscar el ProgressUnit específico para el user_id_hash actual
            for pu in cap.progress_units: # Iterar sobre los progress_units cargados
                if pu.user_id_hash == user_id_hash:
                    progreso_capitulo_especifico = pu
                    break # Encontrado
            
            capitulos_data.append(
                ProgresoCapituloParaProfesor(
                    id_capitulo=cap.id,
                    titulo_capitulo=cap.titulo,
                    estado=progreso_capitulo_especifico.state if progreso_capitulo_especifico else UserChapterStatus.NO_INICIADO,
                    porcentaje_completado=progreso_capitulo_especifico.porcentaje if progreso_capitulo_especifico else 0,
                )
            )

        progreso_total_curso = 0
        if capitulos_data:
            progreso_total_curso = sum(c.porcentaje_completado for c in capitulos_data) // len(capitulos_data)
        
        cursos_progreso.append(
            ProgresoCursoParaProfesor(
                id_curso=curso_obj.id,
                nombre_curso=curso_obj.nombre,
                progreso_general_curso=progreso_total_curso,
                capitulos=capitulos_data
            )
        )
    return cursos_progreso


async def get_progreso_global_alumno(
    db: AsyncSession, 
    user_id_hash: str
) -> ProgresoAlumnoGlobal:
    """
    Obtiene el progreso global de un alumno, incluyendo XP total, racha actual, etc.
    Esto es un ejemplo, puedes expandirlo según necesites.
    """
    user_progress_stmt = select(UserProgress).where(UserProgress.user_id_hash == user_id_hash)
    user_progress_result = await db.execute(user_progress_stmt)
    user_progress_obj = user_progress_result.scalars().first()

    if not user_progress_obj:
        return ProgresoAlumnoGlobal(
            user_id_hash=user_id_hash,
            xp_total=0,
            racha_actual=0,
        )
    
    return ProgresoAlumnoGlobal(
        user_id_hash=user_progress_obj.user_id_hash,
        xp_total=user_progress_obj.total_xp,
        racha_actual=user_progress_obj.current_streak
    )

async def get_all_user_progress_by_user_id_hash(db: AsyncSession, *, user_id_hash: str) -> list[UserProgress]:
    """
    Obtiene todos los registros de UserProgress para un user_id_hash específico.
    Esto permite sumar el XP total de todos los cursos y ver el progreso en cada uno.
    """
    result = await db.execute(
        select(UserProgress).filter(UserProgress.user_id_hash == user_id_hash)
    )
    return result.scalars().all() 