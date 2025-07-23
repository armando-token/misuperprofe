"""
Endpoints simplificados para lecciones sin OAuth Team.
Usa solo Bearer Token para autenticación.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, timedelta
import uuid
import logging
from typing import Optional, List

from app.db.session import get_session
from app.models.adaptive import LessonSession, UserProgress, Attempt, SpacedRepetition
from app.models.curso import Curso
from app.models.capitulo import Capitulo
from app.services.spaced_repetition_logic import update_spaced_repetition_for_item
from app.tools.redis_utils import add_xp_leaderboard, get_leaderboard
from app.api.log import generar_user_id_hash
from app.config import settings

router = APIRouter(prefix="/simple_lesson", tags=["simple_lesson"])
logger = logging.getLogger(__name__)

# Modelos Pydantic
class StartSimpleLessonRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    user_id: str
    course: str
    topic: Optional[str] = None
    chapter_id: Optional[int] = None

class StartSimpleLessonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    session_id: str
    started_at: datetime
    course: str
    topic: Optional[str] = None
    chapter_id: int
    chapter_title: str
    chapter_content: str
    message: str

class AnswerSimpleLessonRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    session_id: str
    answer: str
    # Campos opcionales para compatibilidad
    user_id: Optional[str] = None
    is_correct: Optional[bool] = None
    question_id: Optional[str] = None
    course: Optional[str] = None
    topic: Optional[str] = None

class AnswerSimpleLessonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    next_chapter_id: Optional[int] = None
    next_chapter_title: Optional[str] = None
    next_chapter_content: Optional[str] = None
    xp_earned: int
    message: str
    lesson_completed: bool = False

class CompleteSimpleLessonRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    session_id: str
    user_id: str

class CompleteSimpleLessonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    total_xp: int
    accuracy: float
    duration_minutes: int
    message: str

def verify_bearer_token(request: Request):
    """Verifica el Bearer token."""
    auth = request.headers.get("Authorization")
    if not auth or auth != f"Bearer {settings.API_KEY}":
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True

@router.post("/start", response_model=StartSimpleLessonResponse)
async def start_simple_lesson(
    data: StartSimpleLessonRequest,
    request: Request,
    db: AsyncSession = Depends(get_session)
):
    """
    Inicia una lección simplificada para un usuario.
    """
    verify_bearer_token(request)
    
    try:
        user_id_hash = generar_user_id_hash(data.user_id)
        
        # Verificar si hay una sesión activa
        active_session_result = await db.execute(
            select(LessonSession).filter(
                LessonSession.user_id_hash == user_id_hash,
                LessonSession.ended_at.is_(None)
            )
        )
        active_session = active_session_result.scalars().first()
        
        if active_session:
            # Reutilizar sesión activa
            session_id = str(active_session.id)
            logger.info(f"Reutilizando sesión activa: {session_id}")
        else:
            # Crear nueva sesión
            session_id = str(uuid.uuid4())
            new_session = LessonSession(
                id=uuid.UUID(session_id),
                user_id_hash=user_id_hash,
                course=data.course,
                topic=data.topic,
                started_at=datetime.utcnow()
            )
            db.add(new_session)
            await db.commit()
            logger.info(f"Nueva sesión creada: {session_id}")
        
        # Obtener capítulo para la lección
        if data.chapter_id:
            chapter_result = await db.execute(
                select(Capitulo).filter(Capitulo.id == data.chapter_id)
            )
            chapter = chapter_result.scalars().first()
        else:
            # Obtener primer capítulo del curso
            chapter_result = await db.execute(
                select(Capitulo)
                .join(Curso)
                .filter(Curso.nombre.ilike(f"%{data.course}%"))
                .order_by(Capitulo.orden)
                .limit(1)
            )
            chapter = chapter_result.scalars().first()
        
        if not chapter:
            raise HTTPException(status_code=404, detail=f"No se encontró contenido para el curso '{data.course}'")
        
        # Actualizar sesión con chapter_id
        if active_session:
            active_session.chapter_id = chapter.id
            await db.commit()
        
        # Preparar contenido del capítulo
        content = chapter.contenido_html or chapter.contenido_md or ""
        # Limpiar HTML si es necesario
        import re
        content = re.sub(r'<[^>]+>', '', content)
        
        return StartSimpleLessonResponse(
            session_id=session_id,
            started_at=datetime.utcnow(),
            course=data.course,
            topic=data.topic,
            chapter_id=chapter.id,
            chapter_title=chapter.titulo,
            chapter_content=content[:500] + "..." if len(content) > 500 else content,
            message=f"Lección iniciada en {data.course}. Capítulo: {chapter.titulo}"
        )
        
    except Exception as e:
        logger.error(f"Error en start_simple_lesson: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router.post("/answer", response_model=AnswerSimpleLessonResponse)
async def answer_simple_lesson(
    data: AnswerSimpleLessonRequest,
    request: Request,
    db: AsyncSession = Depends(get_session)
):
    """
    Registra la respuesta del usuario y obtiene el siguiente capítulo.
    """
    verify_bearer_token(request)
    
    try:
        # Obtener información de la sesión activa
        session_result = await db.execute(
            select(LessonSession).filter(LessonSession.session_id == data.session_id)
        )
        active_session = session_result.scalars().first()
        
        if not active_session:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")
        
        # Usar datos de la sesión si no se proporcionan
        user_id = data.user_id or active_session.user_id
        course = data.course or active_session.course
        topic = data.topic or active_session.topic
        question_id = data.question_id or str(active_session.chapter_id or 1)
        
        user_id_hash = generar_user_id_hash(user_id)
        
        # Determinar si la respuesta es correcta (simplificado)
        # En un sistema real, esto debería verificar contra la respuesta correcta
        is_correct = data.is_correct if data.is_correct is not None else True  # Por ahora asumimos correcto
        
        # Registrar el intento
        attempt = Attempt(
            user_id_hash=user_id_hash,
            question_id=question_id,
            answer=data.answer,
            is_correct=is_correct,
            course=course,
            topic=topic
        )
        db.add(attempt)
        
        # Actualizar repetición espaciada si la respuesta es correcta
        if data.is_correct:
            await update_spaced_repetition_for_item(
                db, user_id_hash, data.course, int(data.question_id), True
            )
            # Agregar XP al leaderboard
            add_xp_leaderboard("global_weekly", user_id_hash, 1)
        
        await db.commit()
        
        # Obtener siguiente capítulo
        next_chapter_result = await db.execute(
            select(Capitulo)
            .join(Curso)
            .filter(Curso.nombre.ilike(f"%{data.course}%"))
            .filter(Capitulo.id > int(data.question_id))
            .order_by(Capitulo.orden)
            .limit(1)
        )
        next_chapter = next_chapter_result.scalars().first()
        
        xp_earned = 1 if data.is_correct else 0
        lesson_completed = next_chapter is None
        
        if next_chapter:
            content = next_chapter.contenido_html or next_chapter.contenido_md or ""
            import re
            content = re.sub(r'<[^>]+>', '', content)
            
            return AnswerSimpleLessonResponse(
                next_chapter_id=next_chapter.id,
                next_chapter_title=next_chapter.titulo,
                next_chapter_content=content[:500] + "..." if len(content) > 500 else content,
                xp_earned=xp_earned,
                message=f"¡{'Correcto' if data.is_correct else 'Incorrecto'}! Siguiente capítulo: {next_chapter.titulo}",
                lesson_completed=False
            )
        else:
            return AnswerSimpleLessonResponse(
                xp_earned=xp_earned,
                message=f"¡{'Correcto' if data.is_correct else 'Incorrecto'}! Lección completada.",
                lesson_completed=True
            )
        
    except Exception as e:
        logger.error(f"Error en answer_simple_lesson: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router.post("/complete", response_model=CompleteSimpleLessonResponse)
async def complete_simple_lesson(
    data: CompleteSimpleLessonRequest,
    request: Request,
    db: AsyncSession = Depends(get_session)
):
    """
    Completa una lección y calcula estadísticas.
    """
    verify_bearer_token(request)
    
    try:
        user_id_hash = generar_user_id_hash(data.user_id)
        
        # Obtener sesión activa
        session_result = await db.execute(
            select(LessonSession).filter(
                LessonSession.id == uuid.UUID(data.session_id),
                LessonSession.user_id_hash == user_id_hash
            )
        )
        session = session_result.scalars().first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")
        
        # Calcular estadísticas
        attempts_result = await db.execute(
            select(func.count(Attempt.id), func.sum(func.cast(Attempt.is_correct, func.Integer)))
            .filter(Attempt.user_id_hash == user_id_hash)
            .filter(Attempt.course == session.course)
        )
        total_attempts, correct_attempts = attempts_result.first()
        
        accuracy = (correct_attempts / total_attempts * 100) if total_attempts > 0 else 0
        duration = (datetime.utcnow() - session.started_at).total_seconds() / 60
        
        # Marcar sesión como completada
        session.ended_at = datetime.utcnow()
        session.lesson_xp = int(accuracy * 10)  # XP basado en precisión
        session.accuracy = accuracy / 100
        session.items_completed = total_attempts
        
        await db.commit()
        
        return CompleteSimpleLessonResponse(
            total_xp=int(accuracy * 10),
            accuracy=accuracy,
            duration_minutes=int(duration),
            message=f"Lección completada con {accuracy:.1f}% de precisión en {int(duration)} minutos."
        )
        
    except Exception as e:
        logger.error(f"Error en complete_simple_lesson: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router.get("/progress/{user_id}")
async def get_simple_lesson_progress(
    user_id: str,
    course: Optional[str] = Query(None),
    request: Request = None
):
    """
    Obtiene el progreso de lecciones de un usuario.
    """
    verify_bearer_token(request)
    
    try:
        user_id_hash = generar_user_id_hash(user_id)
        
        # Obtener estadísticas
        query = select(func.count(Attempt.id), func.sum(func.cast(Attempt.is_correct, func.Integer)))
        query = query.filter(Attempt.user_id_hash == user_id_hash)
        
        if course:
            query = query.filter(Attempt.course.ilike(f"%{course}%"))
        
        result = await get_session().execute(query)
        total_attempts, correct_attempts = result.first()
        
        accuracy = (correct_attempts / total_attempts * 100) if total_attempts > 0 else 0
        
        return {
            "user_id": user_id,
            "total_attempts": total_attempts,
            "correct_attempts": correct_attempts,
            "accuracy_percentage": accuracy,
            "course": course or "todos"
        }
        
    except Exception as e:
        logger.error(f"Error en get_simple_lesson_progress: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}") 