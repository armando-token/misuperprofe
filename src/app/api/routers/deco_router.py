"""
Endpoints REST para el sistema DECO (DEstrezas COgnitivas)
Implementa API para preguntas tipo UNMSM 2025
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

logger = logging.getLogger(__name__)

from app.db.session import get_session as get_db
from app.services.deco.deco_engine import DECOEngine
from app.schemas.deco.deco_schemas import (
    DECOQuestionRequest, DECOAnswerRequest, DECOAnswerResponse,
    DECOProgressRequest, DECOProgressResponse, DECORecommendationRequest,
    DECORecommendationResponse
)
from app.models.curso import Curso
from app.models.capitulo import Capitulo
from app.models.external_user_map import ExternalUserMap
from app.services.pattern_service import get_pattern_service
from sqlalchemy import select, func
from app.services.spaced_repetition_logic import update_spaced_repetition_for_item
from app.models.adaptive import Attempt, SpacedRepetition
from app.models.base import Base
from app.config import settings

# Instancia del motor DECO
deco_engine = DECOEngine()

from app.tools.redis_utils import add_xp_leaderboard

router = APIRouter(prefix="/deco", tags=["DECO - Destrezas Cognitivas"])


@router.post("/question")
async def get_deco_question(
    request: DECOQuestionRequest,
    db: Session = Depends(get_db)
):
    """
    Prepara la "receta" para que el Custom GPT genere una pregunta DECO.
    Busca el área del usuario, encuentra el patrón de estilo correspondiente
    y lo combina con el extracto de teoría del capítulo solicitado.
    """
    logger.info(f"Solicitud de receta DECO recibida: {request.dict()}")

    if request.chapter_id is None:
        raise HTTPException(status_code=400, detail="El campo 'chapter_id' es obligatorio.")
    if not request.user_id:
        raise HTTPException(status_code=400, detail="El campo 'user_id' es obligatorio.")

    # 1. Buscar el área del usuario y verificar que esté definida
    user_map_result = await db.execute(
        select(ExternalUserMap).where(ExternalUserMap.external_user_identifier == request.user_id)
    )
    user_map = user_map_result.scalars().first()
    
    if not user_map:
        # Si no existe, lo creamos con el área proporcionada (si existe) o nula.
        # Esto permite que el flujo continúe y luego se le pida al usuario que confirme su área.
        logger.warning(f"Usuario '{request.user_id}' no encontrado. Creando un registro temporal.")
        user_map = ExternalUserMap(
            external_user_identifier=request.user_id,
            assigned_misuperprofe_role='student' # Rol por defecto
        )
        db.add(user_map)
        await db.commit()
        await db.refresh(user_map)

    if not user_map.area:
        logger.error(f"PRECONDICIÓN FALLIDA: Usuario '{request.user_id}' no tiene un área definida.")
        raise HTTPException(
            status_code=412,
            detail="El área del usuario no está definida. Por favor, primero pregunta al usuario a qué área pertenece (A, B, C, D o E) y usa la acción 'set_user_area' para establecerla."
        )
    
    user_area = user_map.area.value

    # 2. Buscar curso y capítulo (la materia es el nombre del curso)
    curso_result = await db.execute(
        select(Curso).where(Curso.nombre.ilike(f"%{request.area}%"))
    )
    curso = curso_result.scalars().first()
    if not curso:
        raise HTTPException(status_code=404, detail=f"El curso '{request.area}' no fue encontrado.")

    capitulo_result = await db.execute(
        select(Capitulo).where(
            Capitulo.curso_id == curso.id,
            Capitulo.orden == request.chapter_id
        )
    )
    capitulo = capitulo_result.scalars().first()
    if not capitulo:
        raise HTTPException(status_code=404, detail=f"El capítulo con orden {request.chapter_id} no fue encontrado en el curso '{request.area}'.")

    # 3. Obtener el patrón DECO
    pattern_service = get_pattern_service()
    subject_name = curso.nombre.capitalize()
    logger.info(f"Buscando patrón DECO con Area='{user_area}' y Subject='{subject_name}'")
    deco_pattern = pattern_service.get_pattern(user_area, subject_name)

    # 4. Construir la respuesta ("receta")
    theory_extract = capitulo.contenido_md or "No hay contenido disponible para este capítulo."
    
    receta_response = {
        "theory_extract": theory_extract,
        "deco_pattern": {
            "user_area": user_area,
            "subject": subject_name,
            **deco_pattern
        },
        "metadata": {
            "course_id": curso.id,
            "chapter_id": capitulo.id,
            "chapter_title": capitulo.titulo
        }
    }

    logger.info(f"Receta DECO preparada para el usuario '{request.user_id}': Area={user_area}, Materia={subject_name}")
    return receta_response


@router.post("/answer", response_model=DECOAnswerResponse)
async def submit_deco_answer(
    request: DECOAnswerRequest,
    db: Session = Depends(get_db)
):
    """
    Evalúa respuesta a pregunta DECO y genera retroalimentación
    """
    try:
        # La lógica de evaluación ahora reside en el Custom GPT.
        # El backend solo registra el intento basado en lo que el GPT informa.
        is_correct = request.is_correct
        
        # La retroalimentación y los puntos se basan en si el GPT marcó la respuesta como correcta.
        feedback = "Respuesta correcta registrada." if is_correct else "Respuesta incorrecta registrada."
        points_earned = 10 if is_correct else 2

        # Otorgar puntos y verificar logros
        await add_xp_leaderboard('global_weekly', request.user_id, points_earned)
        # await check_achievements(request.user_id, db) # La verificación de logros se puede añadir aquí en el futuro
        
        # Guardar intento en base de datos usando datos del request
        attempt = Attempt(
            user_id_hash=request.user_id,
            question_id=request.session_id, # Este es el título del capítulo
            answer=request.answer,
            is_correct=is_correct,
            course=request.area, # Usar área del request
            topic=request.topic,   # Usar tema del request
            created_at=datetime.utcnow()
        )
        db.add(attempt)
        await db.commit()
        
        return DECOAnswerResponse(
            session_id=request.session_id,
            user_id=request.user_id,
            is_correct=is_correct,
            user_answer=request.answer,
            correct_answer="N/A", # El backend ya no conoce la respuesta correcta
            feedback=feedback,
            micro_lesson=feedback,
            cognitive_skill="N/A", # El backend ya no conoce la habilidad
            topic=request.topic,
            area=request.area,
            difficulty=0, # El backend ya no conoce la dificultad
            points_earned=points_earned,
            created_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error en /answer: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error evaluando respuesta DECO: {str(e)}")


@router.get("/progress", response_model=DECOProgressResponse)
async def get_deco_progress(
    user_id: str = Query(..., description="ID del usuario"),
    area: Optional[str] = Query(None, description="Área específica"),
    topic: Optional[str] = Query(None, description="Tema específico"),
    days: int = Query(9999, description="Días hacia atrás"),
    db: Session = Depends(get_db)
):
    """
    Obtiene progreso DECO del usuario
    """
    try:
        # Calcular fecha límite
        date_limit = datetime.utcnow() - timedelta(days=days)
        
        # Construir query base usando sintaxis async
        stmt = select(Attempt).where(
            Attempt.user_id_hash == user_id,
            Attempt.created_at >= date_limit
        )
        
        # Filtrar por área si se especifica
        if area:
            stmt = stmt.where(Attempt.course == area)
        
        # Filtrar por tema si se especifica
        if topic:
            stmt = stmt.where(Attempt.topic == topic)
        
        # Obtener intentos
        result = await db.execute(stmt)
        attempts = result.scalars().all()
        
        # Calcular estadísticas
        total_sessions = len(attempts)
        correct_answers = len([a for a in attempts if a.is_correct])
        incorrect_answers = total_sessions - correct_answers
        accuracy_rate = (correct_answers / total_sessions * 100) if total_sessions > 0 else 0
        
        # Obtener temas cubiertos
        topics_covered = list(set([a.topic for a in attempts]))
        
        # TODO: Implementar tracking de habilidades cognitivas
        cognitive_skills_practiced = ["aplicación", "análisis", "interpretación"]
        
        # Calcular dificultad promedio
        average_difficulty = 2.0  # TODO: Implementar tracking de dificultad
        
        # Calcular puntos totales
        total_points = sum([10 if a.is_correct else 2 for a in attempts])
        
        # Progreso por área
        progress_by_area = {}
        for attempt in attempts:
            area_name = attempt.course
            if area_name not in progress_by_area:
                progress_by_area[area_name] = {
                    "total": 0,
                    "correct": 0,
                    "accuracy": 0.0
                }
            progress_by_area[area_name]["total"] += 1
            if attempt.is_correct:
                progress_by_area[area_name]["correct"] += 1
        
        # Calcular precisión por área
        for area_data in progress_by_area.values():
            if area_data["total"] > 0:
                area_data["accuracy"] = (area_data["correct"] / area_data["total"]) * 100
        
        # Progreso por tema
        progress_by_topic = {}
        for attempt in attempts:
            topic_name = attempt.topic
            if topic_name not in progress_by_topic:
                progress_by_topic[topic_name] = {
                    "total": 0,
                    "correct": 0,
                    "accuracy": 0.0
                }
            progress_by_topic[topic_name]["total"] += 1
            if attempt.is_correct:
                progress_by_topic[topic_name]["correct"] += 1
        
        # Calcular precisión por tema
        for topic_data in progress_by_topic.values():
            if topic_data["total"] > 0:
                topic_data["accuracy"] = (topic_data["correct"] / topic_data["total"]) * 100
        
        return DECOProgressResponse(
            user_id=user_id,
            total_sessions=total_sessions,
            correct_answers=correct_answers,
            incorrect_answers=incorrect_answers,
            accuracy_rate=accuracy_rate,
            topics_covered=topics_covered,
            cognitive_skills_practiced=cognitive_skills_practiced,
            average_difficulty=average_difficulty,
            total_points=total_points,
            progress_by_area=progress_by_area,
            progress_by_topic=progress_by_topic,
            created_at=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo progreso DECO: {str(e)}")


@router.post("/recommendations", response_model=DECORecommendationResponse)
async def get_deco_recommendations(
    request: DECORecommendationRequest,
    db: Session = Depends(get_db)
):
    """
    Genera recomendaciones personalizadas basadas en progreso DECO
    """
    try:
        # TODO: Implementar algoritmo de recomendaciones
        # Por ahora, recomendaciones básicas
        
        recommended_topics = [
            {"topic": "funciones logarítmicas", "priority": 0.9, "reason": "Área débil identificada"},
            {"topic": "geometría analítica", "priority": 0.8, "reason": "Necesita más práctica"},
            {"topic": "trigonometría", "priority": 0.7, "reason": "Tema frecuente en exámenes"}
        ]
        
        recommended_cognitive_skills = ["aplicación", "análisis", "interpretación"]
        
        study_plan = {
            "daily_goal": "3 sesiones DECO",
            "weekly_focus": "Matemáticas y Física",
            "weak_areas": ["funciones", "geometría"],
            "strong_areas": ["álgebra", "aritmética"]
        }
        
        weak_areas = ["funciones", "geometría", "trigonometría"]
        strong_areas = ["álgebra", "aritmética", "estadística"]
        
        next_session_recommendation = {
            "area": "matematicas",
            "topic": "funciones logarítmicas",
            "difficulty": 2,
            "cognitive_skill": "aplicación"
        }
        
        return DECORecommendationResponse(
            user_id=request.user_id,
            recommended_topics=recommended_topics,
            recommended_cognitive_skills=recommended_cognitive_skills,
            study_plan=study_plan,
            weak_areas=weak_areas,
            strong_areas=strong_areas,
            next_session_recommendation=next_session_recommendation,
            created_at=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando recomendaciones DECO: {str(e)}")


@router.get("/cognitive-skills")
async def get_cognitive_skills():
    """
    Obtiene lista de habilidades cognitivas disponibles
    """
    return {
        "cognitive_skills": deco_engine.cognitive_skills,
        "descriptions": {
            "análisis": "Descomponer información en partes para entender su estructura",
            "inferencia": "Sacar conclusiones basadas en evidencia disponible",
            "extrapolación": "Extender información conocida a situaciones nuevas",
            "aplicación": "Usar conocimiento en situaciones prácticas",
            "síntesis": "Combinar elementos para formar un todo coherente",
            "evaluación": "Juzgar el valor o calidad de información",
            "interpretación": "Explicar el significado de información",
            "comparación": "Identificar similitudes y diferencias"
        }
    } 