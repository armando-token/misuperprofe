"""
Router dinámico que maneja todas las operaciones con un solo endpoint.
Inspirado en el servidor antiguo que funcionaba perfectamente.
"""

import logging
from fastapi import APIRouter, Depends, Body, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional
import json
from collections import defaultdict
from sqlalchemy import select

from app.db.session import get_session
from app.models.curso import Curso
from app.models.capitulo import Capitulo
from app.models.adaptive import UserProgress, ProgressUnit, Attempt
from app.services.progress_report_service import ProgressReportService
from app.schemas.dynamic_schemas import UserProgressResponse, UserProgressData, ProgressByCourse


logger = logging.getLogger(__name__)
dynamic_router = APIRouter()

@dynamic_router.post("/api/v1/dynamic")
async def dynamic_endpoint(
    request: Request,
    payload: Dict[str, Any] = Body(...),
    session: AsyncSession = Depends(get_session)
):
    """
    Endpoint dinámico único que maneja todas las operaciones.
    Se adapta según el campo 'action' en el payload.
    """
    # LOG DETALLADO DE LA PETICIÓN
    logger.info("🚨 [DEBUG] PETICIÓN RECIBIDA")
    logger.info(f"🚨 [DEBUG] URL: {request.url}")
    logger.info(f"🚨 [DEBUG] Método: {request.method}")
    logger.info(f"🚨 [DEBUG] Headers: {dict(request.headers)}")
    logger.info(f"🚨 [DEBUG] Payload: {payload}")
    logger.info("🚨 [DEBUG] FIN DE LOG")
    
    action = payload.get("action")
    if not action:
        raise HTTPException(status_code=400, detail="Campo 'action' es requerido")
    
    try:
        if action == "get_courses":
            return await _handle_get_courses(session)
        elif action == "get_question":
            return await _handle_get_question(payload, session)
        elif action == "get_progress":
            return await _handle_get_progress(payload, session)
        elif action == "get_stats":
            return await _handle_get_stats(payload, session)
        elif action == "practice":
            return await _handle_practice(payload, session)
        elif action == "explain":
            return await _handle_explain(payload, session)
        elif action == "help":
            return await _handle_help()
        else:
            raise HTTPException(status_code=400, detail=f"Acción '{action}' no soportada")
    
    except Exception as e:
        logger.error(f"❌ [DYNAMIC] Error en acción '{action}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

async def _handle_get_courses(session: AsyncSession) -> Dict[str, Any]:
    """Maneja la acción get_courses"""
    logger.info("📚 [DYNAMIC] Obteniendo lista de cursos")
    
    result = await session.execute(select(Curso))
    cursos = result.scalars().all()
    
    courses_data = []
    for curso in cursos:
        # Contar capítulos
        chapters_result = await session.execute(
            select(Capitulo).where(Capitulo.curso_id == curso.id)
        )
        chapters_count = len(chapters_result.scalars().all())
        
        courses_data.append({
            "id": curso.nombre.lower().replace(" ", "_"),
            "name": curso.nombre,
            "description": curso.descripcion or f"Curso de {curso.nombre}",
            "chapters": chapters_count
        })
    
    response = {
        "success": True,
        "data": {
            "courses": courses_data,
            "total": len(courses_data)
        },
        "message": "Lista de cursos obtenida exitosamente"
    }
    
    logger.info(f"✅ [DYNAMIC] Respuesta exitosa: {response}")
    return response

async def _handle_get_question(payload: Dict[str, Any], session: AsyncSession) -> Dict[str, Any]:
    """Maneja la acción get_question"""
    logger.info(f"❓ [DYNAMIC] Generando pregunta para: {payload}")
    
    course_name = payload.get("course")
    chapter_id = payload.get("chapter")
    
    if not course_name:
        raise HTTPException(status_code=400, detail="Campo 'course' es requerido para get_question")
    
    # Buscar curso
    from sqlalchemy import select, func
    result = await session.execute(
        select(Curso).where(func.lower(Curso.nombre).ilike(f"%{course_name.lower()}%"))
    )
    curso = result.scalars().first()
    
    if not curso:
        raise HTTPException(status_code=404, detail=f"Curso '{course_name}' no encontrado")
    
    # Buscar capítulo si se especifica
    capitulo = None
    if chapter_id:
        try:
            chapter_order = int(chapter_id)
            result = await session.execute(
                select(Capitulo).where(
                    Capitulo.curso_id == curso.id,
                    Capitulo.orden == chapter_order
                )
            )
            capitulo = result.scalars().first()
        except ValueError:
            raise HTTPException(status_code=400, detail="chapter debe ser un número")
    
    # Generar pregunta dinámica
    question_data = {
        "pregunta": f"¿Cuál es un concepto fundamental de {curso.nombre}?",
        "opciones": [
            "Opción A: Concepto básico",
            "Opción B: Concepto intermedio", 
            "Opción C: Concepto avanzado",
            "Opción D: Ninguna de las anteriores"
        ],
        "respuesta_correcta": "Opción A: Concepto básico",
        "explicacion": f"Esta es una pregunta de práctica sobre {curso.nombre}. Revisa el contenido del capítulo para más detalles."
    }
    
    if capitulo:
        question_data["pregunta"] = f"¿Qué aprendiste en el capítulo '{capitulo.titulo}' de {curso.nombre}?"
        question_data["explicacion"] = f"Este capítulo trata sobre: {capitulo.titulo}"
    
    response = {
        "success": True,
        "data": question_data,
        "message": "Pregunta generada exitosamente"
    }
    
    logger.info(f"✅ [DYNAMIC] Pregunta generada: {response}")
    return response

async def _handle_get_progress(payload: Dict[str, Any], session: AsyncSession) -> Dict[str, Any]:
    """
    Maneja la acción get_progress.
    Calcula el progreso total y un desglose detallado por curso directamente 
    de la tabla de intentos (attempts) para asegurar datos en tiempo real.
    """
    logger.info(f"📊 [DYNAMIC] Obteniendo progreso detallado para: {payload}")
    
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Campo 'user_id' es requerido para get_progress")

    # Obtener todos los intentos para el usuario
    stmt = select(Attempt).where(Attempt.user_id_hash == user_id)
    result = await session.execute(stmt)
    attempts = result.scalars().all()

    if not attempts:
        # Si no hay intentos, devolver progreso vacío
        progress_data = UserProgressData(
            user_id=user_id,
            total_xp=0,
            current_streak=0,
            total_questions_answered=0,
            correct_answers=0,
            progress_by_course=[]
        )
    else:
        # Calcular progreso por curso
        progress_by_course = defaultdict(lambda: {"xp": 0, "questions": 0, "correct": 0})
        for attempt in attempts:
            course_name = attempt.course
            progress_by_course[course_name]["questions"] += 1
            if attempt.is_correct:
                progress_by_course[course_name]["correct"] += 1
                progress_by_course[course_name]["xp"] += 10
            else:
                progress_by_course[course_name]["xp"] += 2
        
        # Formatear la lista para la respuesta
        progress_list = [
            ProgressByCourse(
                course=course,
                xp=data["xp"],
                questions_answered=data["questions"],
                correct_answers=data["correct"]
            ) for course, data in progress_by_course.items()
        ]

        # Calcular totales
        total_xp = sum(item.xp for item in progress_list)
        total_questions = sum(item.questions_answered for item in progress_list)
        total_correct = sum(item.correct_answers for item in progress_list)

        progress_data = UserProgressData(
            user_id=user_id,
            total_xp=total_xp,
            current_streak=0,  # TODO: Implementar lógica de racha
            total_questions_answered=total_questions,
            correct_answers=total_correct,
            progress_by_course=progress_list
        )

    response_model = UserProgressResponse(
        success=True,
        data=progress_data,
        message="Progreso obtenido exitosamente"
    )
    
    # Devuelve el diccionario del modelo Pydantic para que FastAPI lo serialice
    return response_model.model_dump()

async def _handle_get_stats(payload: Dict[str, Any], session: AsyncSession) -> Dict[str, Any]:
    """Maneja la acción get_stats"""
    logger.info(f"📈 [DYNAMIC] Obteniendo estadísticas")
    
    # Estadísticas generales
    from sqlalchemy import select, func
    total_courses = await session.execute(select(func.count(Curso.id)))
    total_chapters = await session.execute(select(func.count(Capitulo.id)))
    
    stats_data = {
        "total_courses": total_courses.scalar(),
        "total_chapters": total_chapters.scalar(),
        "active_users": 1,  # Placeholder
        "total_questions_answered": 0  # Placeholder
    }
    
    response = {
        "success": True,
        "data": stats_data,
        "message": "Estadísticas obtenidas exitosamente"
    }
    
    logger.info(f"✅ [DYNAMIC] Estadísticas obtenidas: {response}")
    return response

async def _handle_practice(payload: Dict[str, Any], session: AsyncSession) -> Dict[str, Any]:
    """Maneja la acción practice"""
    logger.info(f"🎯 [DYNAMIC] Iniciando práctica: {payload}")
    
    course_name = payload.get("course", "general")
    
    practice_data = {
        "mode": "practice",
        "course": course_name,
        "question_count": 5,
        "time_limit": 300,  # 5 minutos
        "instructions": f"Practica con preguntas de {course_name}. Tienes 5 minutos para responder 5 preguntas."
    }
    
    response = {
        "success": True,
        "data": practice_data,
        "message": "Modo práctica iniciado"
    }
    
    logger.info(f"✅ [DYNAMIC] Práctica iniciada: {response}")
    return response

async def _handle_explain(payload: Dict[str, Any], session: AsyncSession) -> Dict[str, Any]:
    """Maneja la acción explain"""
    logger.info(f"📖 [DYNAMIC] Explicando tema: {payload}")
    
    question = payload.get("question", "")
    course = payload.get("course", "general")
    
    explanation_data = {
        "topic": question or f"Conceptos de {course}",
        "explanation": f"Te explico los conceptos fundamentales de {course}. Este tema es importante para tu preparación DECO UNMSM 2025.",
        "key_points": [
            "Concepto 1: Punto clave importante",
            "Concepto 2: Otro punto fundamental",
            "Concepto 3: Aspecto adicional"
        ],
        "tips": [
            "Revisa siempre el contexto histórico",
            "Relaciona los conceptos entre sí",
            "Practica con preguntas similares"
        ]
    }
    
    response = {
        "success": True,
        "data": explanation_data,
        "message": "Explicación generada exitosamente"
    }
    
    logger.info(f"✅ [DYNAMIC] Explicación generada: {response}")
    return response

async def _handle_help() -> Dict[str, Any]:
    """Maneja la acción help"""
    logger.info("🆘 [DYNAMIC] Mostrando ayuda")
    
    help_data = {
        "available_actions": [
            "get_courses - Obtener lista de cursos disponibles",
            "get_question - Generar pregunta de práctica",
            "get_progress - Ver tu progreso personal",
            "get_stats - Ver estadísticas generales",
            "practice - Iniciar sesión de práctica",
            "explain - Explicar un tema específico",
            "help - Mostrar esta ayuda"
        ],
        "usage_examples": [
            '{"action": "get_courses"}',
            '{"action": "get_question", "course": "historia", "chapter": "1"}',
            '{"action": "get_progress", "user_id": "tu_id"}',
            '{"action": "explain", "question": "¿Qué es la independencia del Perú?"}'
        ]
    }
    
    response = {
        "success": True,
        "data": help_data,
        "message": "Ayuda disponible"
    }
    
    logger.info(f"✅ [DYNAMIC] Ayuda mostrada: {response}")
    return response 