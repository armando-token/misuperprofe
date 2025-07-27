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
    DECOQuestionRequest, DECOTheoryResponse, DECOAnswerRequest, 
    DECOAnswerResponse,
    DECOProgressRequest, DECOProgressResponse, DECORecommendationRequest,
    DECORecommendationResponse
)
from app.models.curso import Curso
from app.models.capitulo import Capitulo
from sqlalchemy import select, func
from app.services.spaced_repetition_logic import update_spaced_repetition_for_item
from app.models.adaptive import Attempt, SpacedRepetition
from app.models.base import Base
from app.config import settings

# Instancia del motor DECO
deco_engine = DECOEngine()

# Funciones mock para desarrollo
async def award_points(user_id: str, action: str, points: int):
    """Función mock para otorgar puntos"""
    print(f"Mock: Otorgando {points} puntos a {user_id} por {action}")
    return True

async def check_achievements(user_id: str, db):
    """Función mock para verificar logros"""
    print(f"Mock: Verificando logros para {user_id}")
    return True

router = APIRouter(prefix="/deco", tags=["DECO - Destrezas Cognitivas"])


@router.post("/question", response_model=DECOTheoryResponse)
async def get_deco_question(
    request: DECOQuestionRequest,
    db: Session = Depends(get_db)
):
    """
    Genera una pregunta DECO usando el motor HÍBRIDO.
    Requiere un `chapter_id` para buscar contenido real en la base de datos.
    Si el contenido no se encuentra, devuelve un error 404.
    """
    logger.info(f"Solicitud DECO Híbrida recibida: {request.dict()}")

    if request.chapter_id is None:
        raise HTTPException(
            status_code=400,
            detail="El campo 'chapter_id' es obligatorio para generar una pregunta."
        )

    # Buscar curso por el 'area' proporcionado
    curso_result = await db.execute(
        select(Curso).where(func.lower(Curso.nombre).ilike(f"%{request.area.lower()}%"))
    )
    curso = curso_result.scalars().first()

    if not curso:
        raise HTTPException(
            status_code=404,
            detail=f"El curso '{request.area}' no fue encontrado."
        )

    # Buscar capítulo por número de orden (chapter_id)
    capitulo_result = await db.execute(
        select(Capitulo).where(
            Capitulo.curso_id == curso.id,
            Capitulo.orden == request.chapter_id
        )
    )
    capitulo = capitulo_result.scalars().first()

    if not capitulo:
        raise HTTPException(
            status_code=404,
            detail=f"El capítulo con orden {request.chapter_id} no fue encontrado en el curso '{request.area}'."
        )
    
    logger.info(f"Capítulo encontrado: '{capitulo.titulo}'. Procediendo a extracción de contenido.")
    content = capitulo.contenido_md or ""
    
    question_data = deco_engine.create_deco_question_from_content(
        content=content,
        topic=capitulo.titulo,
        cognitive_skill=request.cognitive_skill,
        chapter_id=capitulo.id,
        course_name=curso.nombre
    )

    if not question_data:
        raise HTTPException(
            status_code=404,
            detail=f"No se pudo preparar el contenido del capítulo '{capitulo.titulo}' para la generación de preguntas."
        )

    # La respuesta ya no es una pregunta, sino la instrucción para generarla
    return question_data


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
        await award_points(request.user_id, "deco_answer", points_earned)
        await check_achievements(request.user_id, db)
        
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
    days: int = Query(30, description="Días hacia atrás"),
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