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
from app.services.deco.deco_engine import deco_engine
from app.schemas.deco.deco_schemas import (
    DECOQuestionRequest, DECOQuestionResponse, DECOAnswerRequest, 
    DECOAnswerResponse, DECOSessionRequest, DECOSessionResponse,
    DECOProgressRequest, DECOProgressResponse, DECORecommendationRequest,
    DECORecommendationResponse
)
from app.services.spaced_repetition_logic import update_spaced_repetition_for_item
from app.models.adaptive import Attempt, SpacedRepetition
from app.models.base import Base
from app.config import settings

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


@router.post("/question", response_model=DECOQuestionResponse)
async def get_deco_question(
    request: DECOQuestionRequest,
    db: Session = Depends(get_db)
):
    """
    Genera una pregunta DECO con cotexto y destrezas cognitivas
    Implementa la filosofía del examen UNMSM 2025
    """
    try:
        # Intentar obtener contenido del capítulo si se proporciona chapter_id
        chapter_content = None
        if hasattr(request, 'chapter_id') and request.chapter_id:
            try:
                # Buscar el capítulo en la base de datos
                from app.models.curso import Curso
                from app.models.capitulo import Capitulo
                from sqlalchemy import select, func
                
                # Buscar curso por nombre
                result = await db.execute(
                    select(Curso).where(func.lower(Curso.nombre).ilike(f"%{request.area.lower()}%"))
                )
                curso = result.scalars().first()
                
                if curso:
                    # Buscar capítulo por orden
                    result = await db.execute(
                        select(Capitulo).where(
                            Capitulo.curso_id == curso.id,
                            Capitulo.orden == request.chapter_id
                        )
                    )
                    capitulo = result.scalars().first()
                    
                    if capitulo and (capitulo.contenido_md or capitulo.resumen):
                        chapter_content = capitulo.contenido_md or capitulo.resumen
                        logger.info(f"Contenido encontrado para capítulo {request.chapter_id} del curso {request.area}")
            except Exception as e:
                logger.warning(f"No se pudo obtener contenido del capítulo: {e}")
        
        # Generar pregunta DECO
        if chapter_content:
            # Usar contenido del capítulo
            session_data = deco_engine.create_deco_question_from_content(
                content=chapter_content,
                topic=request.topic,
                cognitive_skill=request.cognitive_skill
            )
            # Agregar datos de sesión
            session_data.update({
                "user_id": request.user_id,
                "area": request.area,
                "difficulty": request.difficulty,
                "session_id": f"deco_{request.user_id}_{datetime.utcnow().timestamp()}"
            })
        else:
            # Usar contexto generado (método original)
            session_data = deco_engine.create_deco_session(
                user_id=request.user_id,
                area=request.area,
                topic=request.topic,
                difficulty=request.difficulty
            )
        
        return DECOQuestionResponse(**session_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando pregunta DECO: {str(e)}")


@router.post("/answer", response_model=DECOAnswerResponse)
async def submit_deco_answer(
    request: DECOAnswerRequest,
    db: Session = Depends(get_db)
):
    """
    Evalúa respuesta a pregunta DECO y genera retroalimentación
    """
    try:
        # TODO: Recuperar datos de la sesión desde base de datos
        # Por ahora, simulamos los datos de la pregunta
        session_data = {
            "session_id": request.session_id,
            "user_id": request.user_id,
            "area": "matematicas",  # TODO: Recuperar de BD
            "topic": "funciones",   # TODO: Recuperar de BD
            "difficulty": 2,        # TODO: Recuperar de BD
            "cognitive_skill": "aplicación",  # TODO: Recuperar de BD
            "correct_answer": "A",  # TODO: Recuperar de BD
            "context": "Contexto de la pregunta...",  # TODO: Recuperar de BD
            "question": "Pregunta DECO...",  # TODO: Recuperar de BD
            "alternatives": {"A": "Opción A", "B": "Opción B", "C": "Opción C", "D": "Opción D"},
            "explanation": "Explicación de la respuesta correcta"  # TODO: Recuperar de BD
        }
        
        # Verificar si la respuesta es correcta
        is_correct = request.answer.upper() == session_data["correct_answer"].upper()
        
        # Generar retroalimentación adaptativa
        feedback = deco_engine.generate_feedback(
            user_answer=request.answer,
            correct_answer=session_data["correct_answer"],
            question_data=session_data,
            topic=session_data["topic"]
        )
        
        # Calcular puntos ganados
        points_earned = 10 if is_correct else 2  # Puntos por intento
        
        # Actualizar repetición espaciada si es correcta (temporalmente deshabilitada para DECO)
        # TODO: Implementar tabla específica para repetición espaciada DECO
        if is_correct:
            # Temporalmente deshabilitado hasta resolver problema de foreign key
            pass
        
        # Otorgar puntos y verificar logros
        await award_points(request.user_id, "deco_answer", points_earned)
        await check_achievements(request.user_id, db)
        
        # Guardar intento en base de datos
        attempt = Attempt(
            user_id_hash=request.user_id,
            question_id=request.session_id,
            answer=request.answer,
            is_correct=is_correct,
            course=session_data["area"],
            topic=session_data["topic"],
            created_at=datetime.utcnow()
        )
        db.add(attempt)
        await db.commit()
        
        return DECOAnswerResponse(
            session_id=request.session_id,
            user_id=request.user_id,
            is_correct=is_correct,
            user_answer=request.answer,
            correct_answer=session_data["correct_answer"],
            feedback=feedback,
            micro_lesson=feedback,  # TODO: Separar micro-lección
            cognitive_skill=session_data["cognitive_skill"],
            topic=session_data["topic"],
            area=session_data["area"],
            difficulty=session_data["difficulty"],
            points_earned=points_earned,
            created_at=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error evaluando respuesta DECO: {str(e)}")


@router.post("/session", response_model=DECOSessionResponse)
async def create_deco_session(
    request: DECOSessionRequest,
    db: Session = Depends(get_db)
):
    """
    Crea una sesión completa de práctica DECO
    """
    try:
        session_data = deco_engine.create_deco_session(
            user_id=request.user_id,
            area=request.area,
            topic=request.topic,
            difficulty=request.difficulty
        )
        
        session_data["session_type"] = request.session_type
        
        return DECOSessionResponse(**session_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creando sesión DECO: {str(e)}")


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


@router.get("/areas")
async def get_deco_areas():
    """
    Obtiene áreas académicas disponibles para DECO
    """
    return {
        "areas": list(deco_engine.context_templates.keys()),
        "descriptions": {
            "matematicas": "Matemáticas y razonamiento lógico-matemático",
            "fisica": "Física y ciencias físicas",
            "quimica": "Química y procesos químicos",
            "biologia": "Biología y ciencias de la vida",
            "historia": "Historia y ciencias sociales",
            "lenguaje": "Lenguaje y comunicación"
        }
    } 