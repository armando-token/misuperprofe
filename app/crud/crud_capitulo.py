from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import random
from rapidfuzz import process, fuzz

from app.models.capitulo import Capitulo
from app.models.curso import Curso

async def get_capitulos_by_curso_id(db: AsyncSession, curso_id: int) -> List[Capitulo]:
    """
    Obtiene todos los capítulos para un curso_id específico, ordenados por 'orden'.
    """
    result = await db.execute(
        select(Capitulo)
        .filter(Capitulo.curso_id == curso_id)
        .order_by(Capitulo.orden)
    )
    return list(result.scalars().all())

async def get_random_practice_chapter_for_course_topic(
    db: AsyncSession,
    target_course_name: str,
    target_topic_name: Optional[str] = None
) -> Optional[Tuple[Capitulo, str]]:
    """
    Obtiene un capítulo aleatorio y el nombre del curso encontrado
    para un curso y tema (opcional) dados,
    utilizando fuzzy matching para encontrar el curso y el tema.
    Devuelve (Capitulo, nombre_curso_encontrado) o (None, None).
    """
    # 1. Obtener todos los cursos
    cursos_result = await db.execute(select(Curso))
    all_cursos = cursos_result.scalars().all()
    if not all_cursos:
        return None, None # No hay cursos en la BD

    all_course_names = [c.nombre for c in all_cursos]

    # 2. Encontrar el curso que mejor coincida
    matched_course_name_tuple = process.extractOne(
        target_course_name,
        all_course_names,
        scorer=fuzz.WRatio,
        score_cutoff=70  # Umbral de confianza para el nombre del curso
    )
    
    if not matched_course_name_tuple:
        return None, None # No se encontró curso similar
    
    matched_course_name = matched_course_name_tuple[0]

    # Obtener el objeto Curso completo
    matched_curso_obj = next((c for c in all_cursos if c.nombre == matched_course_name), None)
    if not matched_curso_obj: 
        return None, None

    # 3. Obtener capítulos del curso encontrado
    chapters_result = await db.execute(
        select(Capitulo).filter(Capitulo.curso_id == matched_curso_obj.id)
    )
    course_chapters = chapters_result.scalars().all()

    if not course_chapters:
        return None, None # El curso existe pero no tiene capítulos

    candidate_chapters = course_chapters

    # 4. Si se especifica un tema, filtrar capítulos por tema
    if target_topic_name:
        chapter_titles = [c.titulo for c in course_chapters]
        matched_topic_title_tuple = process.extractOne(
            target_topic_name,
            chapter_titles,
            scorer=fuzz.WRatio,
            score_cutoff=60  # Umbral de confianza para el nombre del tema/capítulo
        )

        if not matched_topic_title_tuple:
            return None, None # Se especificó tema pero no se encontró coincidencia
        
        matched_topic_title = matched_topic_title_tuple[0]
        
        candidate_chapters = [c for c in course_chapters if c.titulo == matched_topic_title]
        if not candidate_chapters:
             return None, None


    # 5. Seleccionar un capítulo aleatorio de los candidatos
    if candidate_chapters:
        selected_chapter = random.choice(candidate_chapters)
        return selected_chapter, matched_curso_obj.nombre # Devuelve capítulo y nombre del curso
    
    return None, None # No se encontraron capítulos candidatos 