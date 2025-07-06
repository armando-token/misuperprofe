import sys
sys.path.append('/app')
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from app.models.curso import Curso
from app.models.capitulo import Capitulo
from app.db.session import get_session as get_db
from app.models.adaptive import UserChapterStatus, ProgressUnit
from app.chapter_schemas import CourseChapterListResponse, ChapterWithProgress, UserProgressState
from app.chapter_schemas import ChapterBasicInfo, CourseChapterBasicListResponse
from app.schemas.curso import CursoPublicoListResponse, CursoPublico

# Nuevas importaciones para la autenticación OAuth Team
from app.api.dependencies_team import get_current_team_user_claims
from app.schemas.token_claims import TokenClaims

router = APIRouter(prefix="/api/courses", tags=["courses"])

@router.get("/{course_name}/chapters", response_model=CourseChapterListResponse)
async def list_course_chapters_with_progress(
    course_name: str,
    page: int = Query(1, ge=1, description="Número de página para paginación"),
    page_size: int = Query(20, ge=1, le=100, description="Cantidad de capítulos por página"),
    db: AsyncSession = Depends(get_db),
    current_claims: TokenClaims = Depends(get_current_team_user_claims)
):
    user_id_hash_from_token = current_claims.sub
    # Buscar el curso
    result = await db.execute(select(Curso).where(Curso.nombre.ilike(f"%{course_name}%")))
    db_course = result.scalars().first()
    if not db_course:
        raise HTTPException(status_code=404, detail=f"Curso '{course_name}' no encontrado.")
    # Obtener el total de capítulos de forma eficiente
    total_result = await db.execute(
        select(func.count()).select_from(Capitulo).where(Capitulo.curso_id == db_course.id)
    )
    total_chapters = total_result.scalar_one()
    offset = (page - 1) * page_size
    result = await db.execute(
        select(Capitulo)
        .where(Capitulo.curso_id == db_course.id)
        .order_by(Capitulo.orden.asc().nulls_last(), Capitulo.id.asc())
        .offset(offset)
        .limit(page_size)
    )
    db_chapters = result.scalars().all()
    chapters_with_progress_list = []
    for chapter in db_chapters:
        result = await db.execute(
            select(ProgressUnit).where(
                ProgressUnit.user_id_hash == user_id_hash_from_token,
                ProgressUnit.chapter_id == chapter.id
            )
        )
        user_progress_db = result.scalars().first()
        if user_progress_db:
            current_status = user_progress_db.state
            if isinstance(current_status, str):
                current_status = current_status.lower()
            current_percentage = user_progress_db.porcentaje
        else:
            current_status = UserChapterStatus.NO_INICIADO.value
            current_percentage = 0
        puede_iniciar_o_continuar = (current_status != UserChapterStatus.COMPLETADO.value)
        estado_usuario_data = UserProgressState(
            status=current_status,
            porcentaje_avance=current_percentage,
            puede_iniciar_o_continuar=puede_iniciar_o_continuar
        )
        chapters_with_progress_list.append(
            ChapterWithProgress(
                chapter_id=str(chapter.id),
                title=chapter.titulo,
                order=chapter.orden,
                estado_usuario=estado_usuario_data
            )
        )
    has_next = (offset + len(chapters_with_progress_list)) < total_chapters
    return CourseChapterListResponse(
        course_name=db_course.nombre,
        chapters=chapters_with_progress_list,
        total=total_chapters,
        page=page,
        page_size=page_size,
        has_next=has_next
    )

@router.get("/{course_name}/chapters/{chapter_id}", response_model=ChapterWithProgress)
async def get_chapter_detail_with_progress(
    course_name: str,
    chapter_id: int = Path(..., description="ID del capítulo a consultar"),
    db: AsyncSession = Depends(get_db),
    current_claims: TokenClaims = Depends(get_current_team_user_claims)
):
    user_id_hash_from_token = current_claims.sub
    # Buscar el curso
    result = await db.execute(select(Curso).where(Curso.nombre.ilike(f"%{course_name}%")))
    db_course = result.scalars().first()
    if not db_course:
        raise HTTPException(status_code=404, detail=f"Curso '{course_name}' no encontrado.")
    # Buscar el capítulo
    result = await db.execute(
        select(Capitulo).where(Capitulo.id == chapter_id, Capitulo.curso_id == db_course.id)
    )
    chapter = result.scalars().first()
    if not chapter:
        raise HTTPException(status_code=404, detail=f"Capítulo '{chapter_id}' no encontrado en el curso '{course_name}'.")
    # Buscar progreso del usuario
    result = await db.execute(
        select(ProgressUnit).where(
            ProgressUnit.user_id_hash == user_id_hash_from_token,
            ProgressUnit.chapter_id == chapter.id
        )
    )
    user_progress_db = result.scalars().first()
    if user_progress_db:
        current_status = user_progress_db.state
        if isinstance(current_status, str):
            current_status = current_status.lower()
        current_percentage = user_progress_db.porcentaje
    else:
        current_status = UserChapterStatus.NO_INICIADO.value
        current_percentage = 0
    puede_iniciar_o_continuar = (current_status != UserChapterStatus.COMPLETADO.value)
    estado_usuario_data = UserProgressState(
        status=current_status,
        porcentaje_avance=current_percentage,
        puede_iniciar_o_continuar=puede_iniciar_o_continuar
    )
    return ChapterWithProgress(
        chapter_id=str(chapter.id),
        title=chapter.titulo,
        order=chapter.orden,
        estado_usuario=estado_usuario_data
    )

@router.get("", response_model=CursoPublicoListResponse)
async def listar_cursos(
    db: AsyncSession = Depends(get_db),
    current_claims: TokenClaims = Depends(get_current_team_user_claims)
):
    # user_id_hash_from_token = current_claims.sub # Disponible si se necesita para logging o personalización
    result = await db.execute(select(Curso).order_by(Curso.id))
    cursos_db = result.scalars().all()
    cursos_publicos = [
        CursoPublico(id=c.id, nombre=c.nombre, descripcion=c.descripcion) for c in cursos_db
    ]
    return CursoPublicoListResponse(cursos=cursos_publicos)

@router.get("/{course_id}/chapters", response_model=CourseChapterBasicListResponse)
async def list_course_chapters_basic(
    course_id: int = Path(..., description="ID del curso para listar sus capítulos"),
    page: int = Query(1, ge=1, description="Número de página para paginación"),
    page_size: int = Query(20, ge=1, le=100, description="Cantidad de capítulos por página"),
    db: AsyncSession = Depends(get_db),
    current_claims: TokenClaims = Depends(get_current_team_user_claims)
):
    # Buscar el curso por ID
    result = await db.execute(select(Curso).where(Curso.id == course_id))
    db_course = result.scalars().first()
    if not db_course:
        raise HTTPException(status_code=404, detail=f"Curso con ID '{course_id}' no encontrado.")

    # Obtener el total de capítulos del curso
    total_result = await db.execute(
        select(func.count(Capitulo.id)).where(Capitulo.curso_id == course_id)
    )
    total_chapters = total_result.scalar_one()

    # Obtener los capítulos paginados
    offset = (page - 1) * page_size
    chapters_query = (
        select(Capitulo)
        .where(Capitulo.curso_id == course_id)
        .order_by(Capitulo.orden.asc().nulls_last(), Capitulo.id.asc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(chapters_query)
    db_chapters = result.scalars().all()

    chapters_basic_info_list = [
        ChapterBasicInfo(
            chapter_id=chapter.id, 
            title=chapter.titulo, 
            order=chapter.orden
        ) for chapter in db_chapters
    ]

    has_next = (offset + len(chapters_basic_info_list)) < total_chapters

    return CourseChapterBasicListResponse(
        course_id=db_course.id,
        course_name=db_course.nombre,
        chapters=chapters_basic_info_list,
        total=total_chapters,
        page=page,
        page_size=page_size,
        has_next=has_next
    ) 