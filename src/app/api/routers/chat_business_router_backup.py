
import logging
from fastapi import APIRouter, Depends, Body, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Dict, Any
import random

from app.db.session import get_session
from app.models.curso import Curso
from app.models.capitulo import Capitulo
from app.schemas.pregunta import QuestionRequest, GeneratedQuestion
# from app.services.chains.generation_chain import get_generation_chain

chat_business_router = APIRouter()
logger = logging.getLogger(__name__)

@chat_business_router.post("/get_question", response_model=GeneratedQuestion)
async def get_question_endpoint(
    payload: QuestionRequest = Body(...),
    session: AsyncSession = Depends(get_session)
):
    """
    [DEPRECADO] Endpoint básico para preguntas simples. 
    USAR /deco/question EN SU LUGAR para preguntas tipo UNMSM 2025.
    """
    logger.info(f"Recibida solicitud para generar pregunta con payload: {payload}")
    
    # 1. Búsqueda flexible de curso (case-insensitive)
    course_name = payload.course
    result = await session.execute(
        select(Curso).where(func.lower(Curso.nombre).ilike(f"%{course_name.lower()}%"))
    )
    curso = result.scalars().first()

    if not curso:
        logger.warning(f"Curso no encontrado para el nombre: '{course_name}'")
        raise HTTPException(
            status_code=404,
            detail=f"No se encontró ningún curso que coincida con '{course_name}'."
        )
    logger.info(f"Curso encontrado: {curso.nombre} (ID: {curso.id})")

    # 2. Búsqueda de capítulo por número de orden
    try:
        chapter_order = int(payload.chapter_id)
    except (ValueError, TypeError):
        logger.error(f"El chapter_id '{payload.chapter_id}' no es un número entero válido.")
        raise HTTPException(
            status_code=400,
            detail="El 'chapter_id' debe ser un número entero."
        )

    result = await session.execute(
        select(Capitulo).where(
            Capitulo.curso_id == curso.id,
            Capitulo.orden == chapter_order
        )
    )
    capitulo = result.scalars().first()

    if not capitulo:
        logger.warning(f"Capítulo con orden {chapter_order} no encontrado en el curso '{curso.nombre}'.")
        raise HTTPException(
            status_code=404,
            detail=f"No se encontró el capítulo {chapter_order} en el curso '{curso.nombre}'."
        )
    logger.info(f"Capítulo encontrado: {capitulo.titulo} (Orden: {capitulo.orden})")

    # 3. Generación de pregunta con IA si hay contenido
    if not capitulo.contenido_md or len(capitulo.contenido_md.strip()) < 20:
        logger.warning(f"Contenido del capítulo '{capitulo.titulo}' es demasiado corto o nulo. Se usará un fallback.")
        # Fallback a una pregunta genérica si no hay suficiente contenido para evitar errores
        return GeneratedQuestion(
            pregunta=f"¿Cuál es un concepto fundamental de {curso.nombre}?",
            opciones=["Opción A", "Opción B", "Opción C", "Opción D"],
            respuesta_correcta="Revisar la teoría del capítulo.",
            explicacion=f"Este es un ejemplo. El capítulo '{capitulo.titulo}' no tiene suficiente contenido para generar una pregunta específica."
        )

    # try:
    #     generation_chain = get_generation_chain()
    #     logger.info(f"Invocando la cadena de generación para el capítulo: {capitulo.titulo}")
    #     response = await generation_chain.ainvoke({"input": capitulo.contenido_md})
    #     logger.info(f"Respuesta de la cadena de generación recibida: {response}")
    #     return response
    # except Exception as e:
    #     logger.exception(f"Error al generar pregunta con IA para el capítulo {capitulo.id}: {e}")
    #     raise HTTPException(
    #         status_code=500,
    #         detail="Ocurrió un error interno al intentar generar la pregunta."
    #     )
    
    # Temporalmente retornamos una pregunta de ejemplo
    return GeneratedQuestion(
        pregunta=f"¿Cuál es un concepto fundamental de {curso.nombre}?",
        opciones=["Opción A", "Opción B", "Opción C", "Opción D"],
        respuesta_correcta="Revisar la teoría del capítulo.",
        explicacion=f"Este es un ejemplo temporal. El capítulo '{capitulo.titulo}' no tiene generación de preguntas habilitada aún."
    ) 