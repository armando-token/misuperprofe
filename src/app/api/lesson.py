from fastapi import APIRouter, Depends, HTTPException, Header, Request, Query, Path
from sqlalchemy.orm import Session
from ..models.adaptive import LessonSession, UserProgress, Streak, LessonError, ProgressUnit, GrowthLog, AchievementsLog, UserChapterStatus, Attempt, SpacedRepetition
from ..models.curso import Curso
from ..models.capitulo import Capitulo
from ..db.session import get_session as get_db
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timedelta, timezone
import uuid
from ..tools.redis_utils import (
    push_lesson_queue, pop_lesson_queue, lesson_queue_size,
    push_error_queue, pop_error_queue, error_queue_size, clear_queues,
    add_xp_leaderboard, get_leaderboard, REDIS_ERROR_FLAG_PREFIX,
    get_user_rank_in_leaderboard
)
from sqlalchemy import desc, asc, func, select, or_, case
from ..services.spaced_repetition_logic import update_spaced_repetition_for_item
from typing import Optional, List 
import redis
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import JSONResponse
import asyncpg
import os
import traceback
import inspect
import json
from ..schemas.resultado import LessonResultCreate
from ..models.resultado import Resultado
from ..config import settings
from ..schemas.user_status_schemas import UserStatusResponse, ChapterProgressInfo, SRSSuggestionInfo, UserProgressData

# Nuevas importaciones para la autenticación OAuth Team
from .dependencies_team import get_current_team_user_claims
from ..schemas.token_claims import TokenClaims

# Asegúrate de que sqlalchemy.orm.selectinload está importado:
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/lesson", tags=["lesson"])

class StartLessonRequest(BaseModel):
    # user_id_hash: str # Eliminado, se obtendrá del token
    course: str
    topic: Optional[str] = None
    unit_id: Optional[int] = None
    chapter_id: Optional[int] = None

class StartLessonResponse(BaseModel):
    session_id: str
    started_at: datetime
    course: str
    topic: Optional[str] = None
    unit_id: int  # Siempre un entero, nunca None
    first_item_id: int  # Siempre un entero, nunca None
    first_item_content: Optional[str] = None
    item_beta_difficulty: float
    user_theta: float

@router.post("/start", response_model=StartLessonResponse)
async def start_lesson(
    data: StartLessonRequest,
    db: AsyncSession = Depends(get_db),
    current_claims: TokenClaims = Depends(get_current_team_user_claims)
):
    logger = logging.getLogger("lesson_start")
    user_id_hash = current_claims.sub
    external_user_identifier = current_claims.external_user_identifier

    logger.debug(f"Solicitud /start recibida para usuario '{user_id_hash}' (ext: {external_user_identifier}): {data}")

    if not external_user_identifier: # Comprobación temprana y crucial
        logger.error(f"CRÍTICO: No hay external_user_identifier en token para usuario {user_id_hash} en /start. Denegando.")
        raise HTTPException(status_code=403, detail="Identificación de usuario externa no disponible para verificar permisos de contenido.")

    try:
        active_session_result = await db.execute(select(LessonSession).filter(
            LessonSession.user_id_hash == user_id_hash,
            LessonSession.ended_at.is_(None)
        ))
        active_session = active_session_result.scalars().first()

        capitulo_para_leccion: Optional[Capitulo] = None
        user_progress_for_theta: Optional[UserProgress] = None

        if active_session:
            logger.info(f"Usuario '{user_id_hash}' ya tiene una sesión activa: '{active_session.id}' para el curso '{active_session.course}'.")
            if data.course and data.course.lower() != active_session.course.lower():
                logger.warning(f"Solicitud para curso '{data.course}' pero existe sesión activa para curso '{active_session.course}'. Devolviendo error 409.")
                raise HTTPException(
                    status_code=409,
                    detail=f"Existe una sesión activa para el curso '{active_session.course}'. Por favor, complétela antes de iniciar una lección en un curso diferente."
                )
            
            logger.debug(f"Reutilizando sesión activa '{active_session.id}'. Obteniendo capítulo ID {active_session.chapter_id} de la sesión.")
            capitulo_sesion_activa_result = await db.execute(
                select(Capitulo).filter(Capitulo.id == active_session.chapter_id).options(selectinload(Capitulo.curso))
            )
            capitulo_para_leccion = capitulo_sesion_activa_result.scalars().first()

            if not capitulo_para_leccion or not capitulo_para_leccion.curso:
                logger.error(f"Error crítico: Capítulo ID '{active_session.chapter_id}' o su curso asociado no encontrado para la sesión activa. Invalidando sesión.")
                active_session.ended_at = datetime.now(timezone.utc)
                await db.commit()
                raise HTTPException(status_code=500, detail="Error al recuperar datos del capítulo o curso de la sesión activa. Por favor, intente iniciar la lección de nuevo.")
            
            logger.info(f"Verificando acceso (Supabase) al capítulo {capitulo_para_leccion.id} ('{capitulo_para_leccion.titulo}') de sesión activa para {external_user_identifier}")
            # --- INICIO DE CAMBIO: Usar ensure_user_material_access ---
            try:
                await ensure_user_material_access(
                    external_user_identifier=external_user_identifier,
                    misuperprofe_chapter_id=capitulo_para_leccion.id
                )
                logger.info(f"Acceso CONCEDIDO (Supabase) al capítulo {capitulo_para_leccion.id} ('{capitulo_para_leccion.titulo}') de la SESIÓN ACTIVA.")
            except HTTPException as e:
                # ensure_user_material_access lanza HTTPException si el acceso es denegado.
                logger.warning(f"Acceso DENEGADO (Supabase) al capítulo {capitulo_para_leccion.id} ('{capitulo_para_leccion.titulo}') de la SESIÓN ACTIVA para usuario {external_user_identifier}. Detalle: {e.detail}")
                # La excepción ya está configurada, simplemente la relanzamos.
                raise
            # --- FIN DE CAMBIO ---

            up_result = await db.execute(select(UserProgress).filter(UserProgress.user_id_hash == user_id_hash, UserProgress.course == capitulo_para_leccion.curso.nombre))
            user_progress_for_theta = up_result.scalars().first()
            
            response_payload = {
                "session_id": str(active_session.id),
                "started_at": active_session.started_at.isoformat(),
                "course": capitulo_para_leccion.curso.nombre,
                "topic": capitulo_para_leccion.titulo,
                "unit_id": capitulo_para_leccion.id,
                "first_item_id": capitulo_para_leccion.id,
                "first_item_content": capitulo_para_leccion.contenido_html,
                "item_beta_difficulty": float(capitulo_para_leccion.beta_difficulty if capitulo_para_leccion.beta_difficulty is not None else 0.0),
                "user_theta": float(user_progress_for_theta.theta if user_progress_for_theta and user_progress_for_theta.theta is not None else 0.0)
            }
            return JSONResponse(content=response_payload, status_code=200)

        # --- Si no hay sesión activa, se crea una nueva ---
        logger.debug(f"No se encontró sesión activa para '{user_id_hash}'. Procediendo a crear una nueva lección para el curso '{data.course}'.")
        curso_result = await db.execute(select(Curso).filter(func.lower(Curso.nombre) == func.lower(data.course)))
        curso = curso_result.scalars().first()
        if not curso:
            logger.warning(f"Curso no encontrado: '{data.course}' para usuario '{user_id_hash}'.")
            raise HTTPException(status_code=404, detail=f"Curso '{data.course}' no encontrado.")

        query_initial_item_base = select(Capitulo).filter(Capitulo.curso_id == curso.id).options(selectinload(Capitulo.curso))
        
        # Lógica de selección de capítulo (prioridad: chapter_id, unit_id, topic, luego SRS/secuencial)
        if data.chapter_id is not None:
            logger.debug(f"Intentando cargar capítulo por chapter_id: {data.chapter_id}")
            cap_res = await db.execute(query_initial_item_base.filter(Capitulo.id == data.chapter_id))
            capitulo_para_leccion = cap_res.scalars().first()
        elif data.unit_id is not None:
            logger.debug(f"Intentando cargar capítulo por unit_id: {data.unit_id}")
            cap_res = await db.execute(query_initial_item_base.filter(Capitulo.id == data.unit_id))
            capitulo_para_leccion = cap_res.scalars().first()
        elif data.topic:
            logger.debug(f"Intentando cargar capítulo por topic: '{data.topic}'")
            cap_res = await db.execute(query_initial_item_base.filter(Capitulo.titulo.ilike(f"%{data.topic}%")).order_by(Capitulo.orden.asc().nulls_last(), Capitulo.id.asc()))
            capitulo_para_leccion = cap_res.scalars().first()
        
        if not capitulo_para_leccion: # Si no se encontró por ID o Topic, intentar SRS
            logger.debug(f"No se especificó/encontró capítulo por ID/Topic. Buscando por SRS para curso '{data.course}'.")
            now_for_srs = datetime.now(timezone.utc)
            sr_due_query = select(SpacedRepetition).filter(
                SpacedRepetition.user_id_hash == user_id_hash,
                SpacedRepetition.course == data.course,
                SpacedRepetition.next_due <= now_for_srs
            ).order_by(SpacedRepetition.next_due.asc())
            
            sr_due_item_result = await db.execute(sr_due_query)
            sr_due_item = sr_due_item_result.scalars().first()

            if sr_due_item:
                logger.info(f"Ítem SRS vencido encontrado: chapter_id {sr_due_item.item_id} para curso {data.course}")
                cap_srs_res = await db.execute(query_initial_item_base.filter(Capitulo.id == sr_due_item.item_id))
                capitulo_para_leccion = cap_srs_res.scalars().first()
                if capitulo_para_leccion:
                    logger.info(f"Capítulo {capitulo_para_leccion.id} ('{capitulo_para_leccion.titulo}') seleccionado para inicio vía SRS.")
                else:
                    logger.warning(f"Ítem SRS vencido {sr_due_item.item_id} no corresponde a un capítulo existente en curso {data.course}. Fallback a secuencial.")
            
            if not capitulo_para_leccion: # Si no hay SRS o el capítulo SRS no se encontró, tomar secuencial
                logger.debug("No se encontró ítem SRS vencido o capítulo SRS no existe/válido. Tomando primer capítulo por orden del curso.")
                cap_seq_res = await db.execute(query_initial_item_base.order_by(Capitulo.orden.asc().nulls_last(), Capitulo.id.asc()))
                capitulo_para_leccion = cap_seq_res.scalars().first()
        
        if not capitulo_para_leccion:
            logger.warning(f"No se encontró capítulo adecuado para iniciar lección. Curso: '{data.course}', Criterios: {data}. Usuario: {user_id_hash}")
            raise HTTPException(status_code=404, detail="No hay capítulos disponibles para este curso según los criterios proporcionados o por defecto.")

        logger.info(f"Capítulo ID {capitulo_para_leccion.id} ('{capitulo_para_leccion.titulo}') determinado para iniciar nueva lección. Verificando acceso (Supabase) para {external_user_identifier}.")
        # --- INICIO DE CAMBIO: Usar ensure_user_material_access ---
        try:
            await ensure_user_material_access(
                external_user_identifier=external_user_identifier,
                misuperprofe_chapter_id=capitulo_para_leccion.id
            )
            logger.info(f"Acceso CONCEDIDO (Supabase) a capítulo {capitulo_para_leccion.id} ('{capitulo_para_leccion.titulo}') para usuario {external_user_identifier}.")
        except HTTPException as e:
            logger.warning(f"Acceso DENEGADO (Supabase) a capítulo {capitulo_para_leccion.id} ('{capitulo_para_leccion.titulo}') para usuario {external_user_identifier}. No se puede iniciar la lección. Detalle: {e.detail}")
            raise
        # --- FIN DE CAMBIO ---

        up_result_new = await db.execute(select(UserProgress).filter(UserProgress.user_id_hash == user_id_hash, UserProgress.course == curso.nombre))
        user_progress_for_theta = up_result_new.scalars().first()
        if not user_progress_for_theta:
            logger.info(f"No existe UserProgress para '{user_id_hash}' y curso '{curso.nombre}'. Creando...")
            user_progress_for_theta = UserProgress(user_id_hash=user_id_hash, course=curso.nombre, theta=0.0)
            db.add(user_progress_for_theta)

        session = LessonSession(
            id=uuid.uuid4(), 
            user_id_hash=user_id_hash,
            course=curso.nombre, 
            topic=capitulo_para_leccion.titulo, 
            chapter_id=capitulo_para_leccion.id, 
            started_at=datetime.now(timezone.utc),
            current_session_streak=0 
        )
        db.add(session)
        await db.commit() 
        await db.refresh(session)
        if user_progress_for_theta and db.object_session(user_progress_for_theta):
             await db.refresh(user_progress_for_theta)
        logger.info(f"Nueva sesión '{session.id}' creada para usuario '{user_id_hash}', capítulo '{capitulo_para_leccion.id}'.")

        response_payload_new = {
            "session_id": str(session.id),
            "started_at": session.started_at.isoformat(),
            "course": curso.nombre,
            "topic": capitulo_para_leccion.titulo,
            "unit_id": capitulo_para_leccion.id,
            "first_item_id": capitulo_para_leccion.id,
            "first_item_content": capitulo_para_leccion.contenido_html,
            "item_beta_difficulty": float(capitulo_para_leccion.beta_difficulty if capitulo_para_leccion.beta_difficulty is not None else 0.0),
            "user_theta": float(user_progress_for_theta.theta if user_progress_for_theta and user_progress_for_theta.theta is not None else 0.0)
        }
        return JSONResponse(content=response_payload_new, status_code=200)

    except HTTPException as http_exc:
        logger.warning(f"HTTPException en /start: {http_exc.status_code} - {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error(f"Excepción inesperada en /start para usuario '{user_id_hash}', datos: {data}. Error: {type(e).__name__} - {str(e)}", exc_info=True)
        # Verificar si db está en una transacción activa antes de intentar rollback
        if 'db' in locals() and hasattr(db, 'in_transaction') and db.in_transaction(): # Corrección aquí
             await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno del servidor al iniciar la lección: {type(e).__name__}")

class AnswerRequest(BaseModel):
    session_id: str
    item_id: str # ID del capítulo o ítem
    is_correct: Optional[bool] = None 
    item_overall_correct: Optional[bool] = None 
    item_accuracy_metric: Optional[float] = None 
    latency_ms: Optional[int] = None
    student_answer: Optional[str] = None

    @field_validator('student_answer', mode='before')
    @classmethod
    def normalize_student_answer(cls, v):
        if v is None:
            return None
        if isinstance(v, (dict, list)):
            return json.dumps(v, ensure_ascii=False)
        return str(v)

class AnswerResponse(BaseModel):
    next_item_id: Optional[int] = None
    next_item_content: Optional[str] = None
    previous_mistake: bool = False
    xp_earned: int = 0
    local_streak: int = 0
    message: Optional[str] = None

@router.post("/answer", response_model=AnswerResponse)
async def submit_answer(
    data: AnswerRequest,
    db: AsyncSession = Depends(get_db),
    current_claims: TokenClaims = Depends(get_current_team_user_claims)
):
    logger = logging.getLogger("lesson_answer")
    user_id_hash_from_token = current_claims.sub
    logger.debug(f"Solicitud /answer recibida para usuario (token) '{user_id_hash_from_token}': {data}")

    try:
        session_result = await db.execute(select(LessonSession).filter(
            LessonSession.id == uuid.UUID(data.session_id),
            LessonSession.ended_at.is_(None)
        ))
        session = session_result.scalars().first()

        if not session:
            logger.warning(f"Sesión no encontrada o ya terminada: '{data.session_id}' para usuario (token) '{user_id_hash_from_token}'.")
            raise HTTPException(status_code=404, detail="Active session not found or already ended.")

        if str(session.user_id_hash) != user_id_hash_from_token:
            logger.error(f"Discrepancia de usuario: Token para '{user_id_hash_from_token}', pero sesión '{data.session_id}' pertenece a '{session.user_id_hash}'.")
            raise HTTPException(status_code=403, detail="User token does not match session owner.")

        user_id_hash = str(session.user_id_hash) # Usar el de la sesión, ya validado

        # Determinar la corrección de la respuesta para lógica SRS y Attempt
        is_correct_for_srs_and_attempt: Optional[bool] = None
        item_id_int = int(data.item_id)

        if data.student_answer and data.student_answer.lower() == "completado":
            is_correct_for_srs_and_attempt = True
            logger.info(f"Respuesta marcada como 'completado' para item {item_id_int} en sesión {session.id}.")
        elif data.item_accuracy_metric is not None:
            ACCURACY_THRESHOLD_FOR_CORRECT = 0.6 # Ejemplo de umbral
            is_correct_for_srs_and_attempt = data.item_accuracy_metric >= ACCURACY_THRESHOLD_FOR_CORRECT
        elif data.item_overall_correct is not None:
            is_correct_for_srs_and_attempt = data.item_overall_correct
        elif data.is_correct is not None: # Legacy
            is_correct_for_srs_and_attempt = data.is_correct
        else:
            # Si no hay forma de determinar la corrección y no es "completado", se asume incorrecto o se lanza error.
            # Por ahora, si es None, update_spaced_repetition_for_item lo tratará como incorrecto.
            # Para Attempt, si la columna is_correct no es nullable, esto sería un problema.
            # Asumimos que si llega aquí sin datos de corrección, es un error de payload o un flujo no esperado.
            logger.warning(f"No se pudo determinar la corrección para item {item_id_int}, sesión {session.id}. Asumiendo incorrecto para SRS y Attempt si es necesario.")
            is_correct_for_srs_and_attempt = False # Default a False si no se puede determinar


        capitulo_result = await db.execute(select(Capitulo).filter(Capitulo.id == item_id_int))
        capitulo = capitulo_result.scalars().first()
        if not capitulo:
            logger.error(f"Capítulo ID '{item_id_int}' no encontrado para procesar respuesta en sesión '{session.id}'.")
            raise HTTPException(status_code=404, detail="Chapter (item) not found.")

        # Registrar el intento (Attempt)
        new_attempt = Attempt(
            user_id_hash=user_id_hash,
            question_id=str(item_id_int),
            answer=data.student_answer,
            is_correct=is_correct_for_srs_and_attempt,
            course=session.course,
            topic=capitulo.titulo 
        )
        db.add(new_attempt)

        # Obtener o crear UserProgress para el curso
        progress_result = await db.execute(select(UserProgress).filter(
            UserProgress.user_id_hash == user_id_hash,
            UserProgress.course == session.course
        ))
        user_progress = progress_result.scalars().first()
        if not user_progress:
            logger.info(f"Creando nuevo UserProgress para usuario '{user_id_hash}', curso '{session.course}' en submit_answer.")
            user_progress = UserProgress(user_id_hash=user_id_hash, course=session.course, theta=0.0, hearts=settings.HEART_MAX_COUNT)
            db.add(user_progress)
            await db.flush() # Asegurar que user_progress tenga ID si se usa inmediatamente

        # Lógica IRT (si aplica item_accuracy_metric)
        if data.item_accuracy_metric is not None:
            user_theta = float(user_progress.theta or 0.0)
            item_beta = float(capitulo.beta_difficulty or 0.0)
            observed_result_for_irt = float(data.item_accuracy_metric)
            
            import math
            exponent = -(user_theta - item_beta)
            try:
                prob_correct_expected = 1 / (1 + math.exp(exponent))
            except OverflowError:
                prob_correct_expected = 0.0 if exponent > 0 else 1.0
            
            K_FACTOR = 0.25
            user_progress.theta = float(user_theta + K_FACTOR * (observed_result_for_irt - prob_correct_expected))
            THETA_MIN, THETA_MAX = -4.0, 4.0 # Configurable
            user_progress.theta = max(THETA_MIN, min(THETA_MAX, float(user_progress.theta)))
            db.add(user_progress)

        # Lógica de XP y racha de sesión
        xp_earned = 0
        SESSION_STREAK_THRESHOLD = 3
        SESSION_STREAK_BONUS_XP = 5
        XP_MAX_PER_ANSWER = 20

        if is_correct_for_srs_and_attempt:
            xp_earned = settings.XP_BASE_POINTS
            session.current_session_streak = (session.current_session_streak or 0) + 1
            if session.current_session_streak % SESSION_STREAK_THRESHOLD == 0: # Bonus cada N respuestas correctas seguidas
                xp_earned += SESSION_STREAK_BONUS_XP
        else:
            if session.current_session_streak and session.current_session_streak > 0:
                logger.info(f"Respuesta incorrecta. Racha de sesión {session.current_session_streak} interrumpida para user {user_id_hash}, session {session.id}")
            session.current_session_streak = 0
            # Registrar error para posible reintento o análisis
            # push_error_queue(user_id_hash, session.id, str(item_id_int)) # Si se usa colas Redis
            error_record = LessonError(session_id=session.id, item_id=str(item_id_int), resolved=False, course=session.course)
            db.add(error_record)
            if user_progress: # Solo descontar si existe user_progress
                user_progress.hearts = max((user_progress.hearts or settings.HEART_MAX_COUNT) - 1, 0)
                db.add(user_progress)


        xp_earned = min(xp_earned, XP_MAX_PER_ANSWER)
        session.lesson_xp = (session.lesson_xp or 0) + xp_earned
        session.items_completed = (session.items_completed or 0) + 1
        # No se actualiza user_progress.total_xp aquí; se hace en complete_lesson.
        db.add(session)

        # Actualizar SpacedRepetition
        sr_item_updated = await update_spaced_repetition_for_item(
            db,
            user_id_hash=user_id_hash,
            course=session.course,
            item_id=item_id_int,
            is_correct_response=is_correct_for_srs_and_attempt
        )

        # Actualizar ProgressUnit basado en el estado de SpacedRepetition
        if sr_item_updated:
            pu_result = await db.execute(select(ProgressUnit).filter(
                ProgressUnit.user_id_hash == user_id_hash,
                ProgressUnit.chapter_id == item_id_int
            ))
            progress_unit = pu_result.scalars().first()

            if not progress_unit:
                progress_unit = ProgressUnit(
                    user_id_hash=user_id_hash,
                    chapter_id=item_id_int,
                    course=session.course,
                    state=UserChapterStatus.NO_INICIADO,
                    porcentaje=0,
                    stars=0
                )
                db.add(progress_unit)

            # Calcular porcentaje y estrellas basado en sr_item_updated
            porcentaje_calculado, stars_calculadas = 0, 0
            if sr_item_updated.difficulty == "hard":
                porcentaje_calculado = 25; stars_calculadas = 1
            elif sr_item_updated.difficulty == "normal":
                porcentaje_calculado = 50
                stars_calculadas = 2 if sr_item_updated.repetition_number >= 2 else 1
            elif sr_item_updated.difficulty == "easy":
                porcentaje_calculado = 75
                if sr_item_updated.repetition_number == 1: stars_calculadas = 2
                elif sr_item_updated.repetition_number >= 2: stars_calculadas = 3
                else: stars_calculadas = 1
            
            if sr_item_updated.repetition_number == 0 and sr_item_updated.times_seen > 0: # Falló recientemente
                porcentaje_calculado = 10 if sr_item_updated.difficulty == "hard" else 20
                stars_calculadas = 0

            if data.student_answer and data.student_answer.lower() == "completado":
                porcentaje_calculado = 100; stars_calculadas = 3
            
            progress_unit.porcentaje = porcentaje_calculado
            progress_unit.stars = stars_calculadas
            if porcentaje_calculado == 100:
                progress_unit.state = UserChapterStatus.COMPLETADO
            elif progress_unit.state == UserChapterStatus.NO_INICIADO or not progress_unit.state:
                 progress_unit.state = UserChapterStatus.EN_PROGRESO
            db.add(progress_unit)

        # Añadir XP al leaderboard
        if xp_earned > 0:
            add_xp_leaderboard(base_league_id="global", user_id=user_id_hash, xp_increment=xp_earned) # Asume que add_xp_leaderboard es síncrona

        # Lógica para determinar el siguiente ítem
        next_item_id_to_return = None
        next_item_content_to_return = None

        # 1. Priorizar errores no resueltos en la sesión actual
        error_result = await db.execute(select(LessonError).filter(
            LessonError.session_id == session.id,
            LessonError.resolved == False
        ).order_by(LessonError.created_at.asc()))
        pending_error = error_result.scalars().first()

        if pending_error:
            try:
                next_item_id_to_return = int(pending_error.item_id)
                # Marcar en Redis que este error se está presentando (si se usa Redis para flags)
                # r = redis.from_url(settings.REDIS_URL)
                # r.set(f"{REDIS_ERROR_FLAG_PREFIX}{session.id}:{pending_error.item_id}", 1, ex=3600)
            except ValueError:
                logger.error(f"Invalid item_id format in LessonError: {pending_error.item_id}")
        
        if not next_item_id_to_return:
            # 2. Priorizar ítems del SRS vencidos
            now_utc = datetime.now(timezone.utc) # Usar timezone.utc
            sr_due_result = await db.execute(select(SpacedRepetition).filter(
                SpacedRepetition.user_id_hash == user_id_hash,
                SpacedRepetition.course == session.course,
                SpacedRepetition.next_due <= now_utc
            ).order_by(SpacedRepetition.next_due.asc()))
            sr_due_item = sr_due_result.scalars().first()
            if sr_due_item:
                next_item_id_to_return = sr_due_item.item_id

        if not next_item_id_to_return and is_correct_for_srs_and_attempt:
            # 3. Si la respuesta fue correcta y no hay errores/SRS, tomar el siguiente capítulo secuencial no completado
            current_capitulo_orden = capitulo.orden if capitulo and capitulo.orden is not None else -1
            
            next_sequential_query = select(Capitulo).outerjoin(
                ProgressUnit, (ProgressUnit.chapter_id == Capitulo.id) & (ProgressUnit.user_id_hash == user_id_hash)
            ).filter(
                Capitulo.curso_id == capitulo.curso_id,
                Capitulo.orden > current_capitulo_orden,
                or_(ProgressUnit.state == None, ProgressUnit.state != UserChapterStatus.COMPLETADO)
            ).order_by(Capitulo.orden.asc())
            
            next_sequential_item_result = await db.execute(next_sequential_query)
            next_sequential_item = next_sequential_item_result.scalars().first()
            if next_sequential_item:
                next_item_id_to_return = next_sequential_item.id
        
        if next_item_id_to_return:
            next_capitulo_result = await db.execute(select(Capitulo).filter(Capitulo.id == next_item_id_to_return))
            next_capitulo_obj = next_capitulo_result.scalars().first()
            if next_capitulo_obj:
                next_item_content_to_return = next_capitulo_obj.contenido_html or next_capitulo_obj.contenido_md or next_capitulo_obj.contenido

        # Resolver flag de error en Redis si la respuesta fue correcta y había un flag
        # r = redis.from_url(settings.REDIS_URL)
        # error_flag_key = f"{REDIS_ERROR_FLAG_PREFIX}{session.id}:{data.item_id}"
        # if is_correct_for_srs_and_attempt and r.exists(error_flag_key):
        #     # Marcar error como resuelto en la BD también
        #     # ...
        #     r.delete(error_flag_key)

        await db.commit()
        logger.info(f"Respuesta /answer para sesión '{session.id}' (usuario '{user_id_hash}') procesada. XP earned: {xp_earned}. Next item: {next_item_id_to_return}")

        return AnswerResponse(
            next_item_id=next_item_id_to_return,
            next_item_content=next_item_content_to_return,
            previous_mistake=not is_correct_for_srs_and_attempt,
            xp_earned=xp_earned,
            local_streak=session.current_session_streak or 0,
            message="Respuesta registrada"
        )

    except HTTPException as http_exc:
        logger.warning(f"HTTPException en /answer para usuario (token) '{user_id_hash_from_token}', sesión '{data.session_id}': {http_exc.detail}")
        await db.rollback() # Rollback en caso de error HTTP explícito
        raise http_exc
    except Exception as e:
        logger.error(f"Error inesperado en /answer para usuario (token) '{user_id_hash_from_token}', sesión '{data.session_id}': {e}", exc_info=True)
        await db.rollback() # Rollback en caso de error inesperado
        raise HTTPException(status_code=500, detail=f"Internal server error processing answer.")

class CompleteLessonRequest(BaseModel):
    session_id: str

class CompleteLessonResponse(BaseModel):
    xp: int
    accuracy: Optional[float] = None
    duration: Optional[int] = None
    claim_token: str

@router.post("/complete", response_model=CompleteLessonResponse)
async def complete_lesson(
    data: CompleteLessonRequest,
    db: AsyncSession = Depends(get_db),
    current_claims: TokenClaims = Depends(get_current_team_user_claims)
):
    logger = logging.getLogger("lesson_complete")
    user_id_hash_from_token = current_claims.sub
    logger.info(f"Solicitud /complete recibida para usuario (token) '{user_id_hash_from_token}', sesión '{data.session_id}'.")

    try:
        session_result = await db.execute(select(LessonSession).filter(
            LessonSession.id == uuid.UUID(data.session_id),
            LessonSession.ended_at.is_(None)
        ))
        session = session_result.scalars().first()

        if not session:
            logger.warning(f"Sesión activa no encontrada para ID '{data.session_id}' en /complete para usuario (token) '{user_id_hash_from_token}'.")
            raise HTTPException(status_code=404, detail="Active session not found for the given ID.")

        if str(session.user_id_hash) != user_id_hash_from_token:
            logger.error(f"Discrepancia de usuario en /complete: Token para '{user_id_hash_from_token}', pero sesión '{data.session_id}' pertenece a '{session.user_id_hash}'.")
            raise HTTPException(status_code=403, detail="User token does not match session owner.")
        
        user_id_hash = str(session.user_id_hash)

        logger.debug(f"Procesando complete_lesson para sesión {session.id}, usuario {user_id_hash}")
        now = datetime.utcnow().replace(tzinfo=None)
        session.ended_at = now
        duration = int((now - session.started_at).total_seconds()) if session.started_at else None
        session.duration = duration

        total_items_in_session = session.items_completed or 1
        
        stmt_errors = select(func.count(LessonError.id)).filter(
            LessonError.session_id == session.id, 
            LessonError.resolved == False
        )
        error_count_result = await db.execute(stmt_errors)
        errors_in_session = error_count_result.scalar_one_or_none() or 0
        
        accuracy_val = round((total_items_in_session - errors_in_session) / total_items_in_session, 3) if total_items_in_session > 0 else 0.0
        session.accuracy = accuracy_val
        logger.debug(f"Sesión {session.id}: Items {total_items_in_session}, Errores {errors_in_session}, Accuracy {accuracy_val}")

        user_progress_result = await db.execute(select(UserProgress).filter(
            UserProgress.user_id_hash == user_id_hash,
            UserProgress.course == session.course
        ))
        progress = user_progress_result.scalars().first()

        current_utc_naive_now_date = datetime.utcnow().date()

        if not progress:
            logger.info(f"Usuario {user_id_hash} (curso {session.course}): Creando UserProgress. Primera actividad, racha actual = 1.")
            progress = UserProgress(
                user_id_hash=user_id_hash,
                course=session.course,
                total_xp=(session.lesson_xp or 0),
                current_streak=1, 
                longest_streak=1,
                last_active=current_utc_naive_now_date,
                hearts=settings.HEART_MAX_COUNT, 
                chests=0 
            )
            db.add(progress)
        else:
            logger.info(f"Usuario {user_id_hash} (curso {session.course}): Actualizando UserProgress existente.")
            
            last_active_date_for_streak = progress.last_active

            if not last_active_date_for_streak:
                progress.current_streak = 1
                logger.info(f"Usuario {user_id_hash} (curso {session.course}): UserProgress existía pero sin last_active_date. Racha actual = 1.")
            else:
                if current_utc_naive_now_date == last_active_date_for_streak:
                    logger.info(f"Usuario {user_id_hash} (curso {session.course}): Ya activo hoy ({last_active_date_for_streak}). Racha sin cambios: {progress.current_streak}.")
                elif current_utc_naive_now_date == last_active_date_for_streak + timedelta(days=1):
                    progress.current_streak = (progress.current_streak or 0) + 1
                    logger.info(f"Usuario {user_id_hash} (curso {session.course}): Día consecutivo. Racha incrementada a: {progress.current_streak}.")
                else:
                    progress.current_streak = 1
                    logger.info(f"Usuario {user_id_hash} (curso {session.course}): Racha interrumpida (Última: {last_active_date_for_streak}, Hoy: {current_utc_naive_now_date}). Nueva racha = 1.")
            
            progress.longest_streak = max((progress.longest_streak or 0), (progress.current_streak or 0))
            progress.last_active = current_utc_naive_now_date
            
            progress.total_xp = (progress.total_xp or 0) + (session.lesson_xp or 0)
            logger.debug(f"Sesión {session.id}: XP de sesión {session.lesson_xp}. UserProgress total_xp actualizado a {progress.total_xp}")

        if settings.XP_PER_CHEST > 0:
            xp_antes_de_esta_leccion_global = (progress.total_xp or 0) - (session.lesson_xp or 0)
            if xp_antes_de_esta_leccion_global < 0: xp_antes_de_esta_leccion_global = 0
            
            cofres_antes = xp_antes_de_esta_leccion_global // settings.XP_PER_CHEST
            cofres_despues = (progress.total_xp or 0) // settings.XP_PER_CHEST
            cofres_ganados_ahora = cofres_despues - cofres_antes

            if cofres_ganados_ahora > 0:
                progress.chests = (progress.chests or 0) + cofres_ganados_ahora
                logger.info(f"Usuario {user_id_hash} ganó {cofres_ganados_ahora} cofres. Total cofres: {progress.chests}")
        
        session.lesson_xp = session.lesson_xp or 0

        if session.chapter_id:
            pu_result = await db.execute(select(ProgressUnit).filter(
                ProgressUnit.user_id_hash == user_id_hash,
                ProgressUnit.chapter_id == session.chapter_id
            ))
            pu = pu_result.scalars().first()

            calculated_stars_on_completion = 0
            if (session.accuracy or 0) >= 0.9: calculated_stars_on_completion = 3
            elif (session.accuracy or 0) >= 0.7: calculated_stars_on_completion = 2
            elif (session.accuracy or 0) > 0: calculated_stars_on_completion = 1
            else: calculated_stars_on_completion = 1 

            if not pu:
                logger.info(f"Creando ProgressUnit para cap {session.chapter_id}, user {user_id_hash}, curso {session.course}")
                pu = ProgressUnit(
                    user_id_hash=user_id_hash,
                    chapter_id=session.chapter_id,
                    course=session.course,
                    state=UserChapterStatus.COMPLETADO,
                    porcentaje=100,
                    stars=calculated_stars_on_completion
                )
                db.add(pu)
            else:
                logger.info(f"Actualizando ProgressUnit existente para cap {session.chapter_id}, user {user_id_hash}")
                pu.state = UserChapterStatus.COMPLETADO
                pu.porcentaje = 100
                pu.stars = calculated_stars_on_completion 
                db.add(pu)
            
            was_successful_overall_for_srs = (session.accuracy or 0) >= 0.6
            logger.debug(f"Actualizando SRS para item {session.chapter_id}, user {user_id_hash}. Correcto: {was_successful_overall_for_srs} (accuracy: {session.accuracy})")
            
            cap_result_for_srs = await db.execute(select(Capitulo.beta_difficulty).filter(Capitulo.id == session.chapter_id))
            current_item_difficulty_for_srs = cap_result_for_srs.scalar_one_or_none()

            await update_spaced_repetition_for_item(
                db_session=db,
                user_id_hash=user_id_hash,
                course_name=session.course,
                item_id=session.chapter_id,
                is_correct_response=was_successful_overall_for_srs,
                current_difficulty=current_item_difficulty_for_srs
            )
        
        db.add(session)
        if progress: 
            db.add(progress)

        await db.commit()
        
        claim_token_val = f"claim-{session.id}-{int(now.timestamp())}"
        logger.info(f"Lección completada exitosamente para sesión {session.id}, usuario {user_id_hash}. XP: {session.lesson_xp}, Accuracy: {session.accuracy}, Duration: {duration}")
        
        return CompleteLessonResponse(
            xp=(session.lesson_xp or 0),
            accuracy=session.accuracy,
            duration=duration,
            claim_token=claim_token_val
        )

    except HTTPException as http_exc:
        logger.warning(f"HTTPException en /complete para usuario (token) '{user_id_hash_from_token}', sesión '{data.session_id}': {http_exc.detail}")
        await db.rollback()
        raise http_exc
    except Exception as e:
        logger.error(f"Error inesperado en /complete para usuario (token) '{user_id_hash_from_token}', sesión '{data.session_id}': {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error interno del servidor durante la finalización de la lección: {type(e).__name__}"
        )

@router.get("/user/status", response_model=UserStatusResponse)
async def user_status(
    db: AsyncSession = Depends(get_db),
    current_claims: TokenClaims = Depends(get_current_team_user_claims),
    course: Optional[str] = Query(None, alias="course")
):
    logger = logging.getLogger("user_status")
    user_id_hash_from_token = current_claims.sub
    course_param = course

    logger.info(f"Solicitud /user/status para usuario (token) '{user_id_hash_from_token}'. Course param: '{course_param}'")

    # --- INICIO DE LÓGICA ORIGINAL MODIFICADA PARA USAR user_id_hash_from_token ---
    # Validar que se ha proporcionado un curso si es necesario para la lógica del endpoint
    if not course_param: # Asumiendo que el curso es obligatorio para este endpoint.
        logger.warning(f"Falta el parámetro 'course' para /user/status, usuario (token) '{user_id_hash_from_token}'")
        raise HTTPException(status_code=400, detail="El parámetro 'course' es requerido.")

    # 1. Obtener UserProgress (datos de gamificación existentes)
    user_progress_stmt = select(UserProgress).filter(
        UserProgress.user_id_hash == user_id_hash_from_token,
        UserProgress.course == course_param
    )
    user_progress_result = await db.execute(user_progress_stmt)
    progress = user_progress_result.scalars().first()

    if not progress:
        # Si no existe, creamos uno nuevo con valores por defecto.
        progress = UserProgress(
            user_id_hash=user_id_hash_from_token,
            course=course_param,
            theta=0.0,
            total_xp=0,
            current_streak=0,
            longest_streak=0,
            last_active=None,
            hearts=settings.HEART_MAX_COUNT,
            chests=0
        )
        db.add(progress)
        await db.commit()
        await db.refresh(progress)

    # 2. Obtener la sesión de lección más reciente para este curso si existe
    latest_session_stmt = select(LessonSession).filter(
        LessonSession.user_id_hash == user_id_hash_from_token,
        LessonSession.course == course_param
    ).order_by(LessonSession.started_at.desc())
    latest_session_result = await db.execute(latest_session_stmt)
    latest_session = latest_session_result.scalars().first()

    if latest_session:
        logger.info(f"Sesión de lección más reciente encontrada para usuario {user_id_hash_from_token}: {latest_session.id}")
        total_xp = latest_session.lesson_xp or 0
        current_streak = latest_session.current_session_streak or 0
        longest_streak = latest_session.longest_session_streak or 0
        last_active_date = latest_session.last_active
        hearts = getattr(latest_session, "hearts", None)
        chests = getattr(latest_session, "chests", None)
    else:
        logger.warning(f"No se encontró ninguna sesión de lección para el usuario {user_id_hash_from_token} y el curso {course_param}")
        total_xp = 0
        current_streak = 0
        longest_streak = 0
        last_active_date = None
        hearts = None
        chests = None

    # 3. Obtener capítulos estudiados
    studied_chapters_info: List[ChapterProgressInfo] = []
    try:
        studied_stmt = (
            select(
                Capitulo.id.label("chapter_id"),
                Capitulo.titulo.label("chapter_title"),
                ProgressUnit.state.label("status"),
                ProgressUnit.porcentaje.label("percentage")
            )
            .join(Capitulo, ProgressUnit.chapter_id == Capitulo.id)
            .where(
                ProgressUnit.user_id_hash == user_id_hash_from_token,
                ProgressUnit.course == course_param # ProgressUnit usa el nombre del curso
            )
            .order_by(Capitulo.orden.asc().nulls_last(), Capitulo.id.asc())
        )
        studied_results = await db.execute(studied_stmt)
        for row in studied_results.mappings().all(): # Usar mappings() para acceder por nombre de columna/label
            studied_chapters_info.append(ChapterProgressInfo(**row))
    except Exception as e:
        logger.error(f"Error obteniendo capítulos estudiados para {user_id_hash_from_token}, curso {course_param}: {e}", exc_info=True)
        # studied_chapters_info permanecerá vacía

    # 4. Obtener sugerencias SRS
    srs_suggestions_info: List[SRSSuggestionInfo] = []
    try:
        srs_stmt = (
            select(
                Capitulo.id.label("chapter_id"),
                Capitulo.titulo.label("chapter_title"),
                SpacedRepetition.next_due
            )
            .join(Capitulo, SpacedRepetition.item_id == Capitulo.id)
            .where(
                SpacedRepetition.user_id_hash == user_id_hash_from_token,
                SpacedRepetition.course == course_param # SpacedRepetition usa el nombre del curso
                # Podríamos añadir un filtro para SpacedRepetition.next_due <= datetime.utcnow() si solo queremos los vencidos
            )
            .order_by(SpacedRepetition.next_due.asc())
            .limit(5) # Limitar a las 5 próximas sugerencias
        )
        srs_results = await db.execute(srs_stmt)
        for row in srs_results.mappings().all():
            srs_suggestions_info.append(SRSSuggestionInfo(**row))
    except Exception as e:
        logger.error(f"Error obteniendo sugerencias SRS para {user_id_hash_from_token}, curso {course_param}: {e}", exc_info=True)
        # srs_suggestions_info permanecerá vacía

    return UserStatusResponse(
        user_id_hash=user_id_hash_from_token,
        course=course_param,
        total_xp=total_xp,
        current_streak=current_streak,
        longest_streak=longest_streak,
        leaderboard_rank_global_weekly=None,
        user_progress=UserProgressData(
            total_lessons_completed=sum(1 for pu in progress_list if pu.state.name != "NO_INICIADO"),
            total_chapters_mastered=sum(1 for pu in progress_units if pu.state.name == "COMPLETADO")
        ),
        overall_accuracy=progress.accuracy if progress else None,
        studied_chapters=studied_chapters_info,
        srs_suggestions=srs_suggestions_info
    )

@router.post("/growth_prompt")
async def growth_prompt(
    user_id_hash: str = Query(...), # Este user_id_hash podría necesitar ser validado contra el token
    prompt_type: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_claims: TokenClaims = Depends(get_current_team_user_claims) # NUEVO: Añadir dependencia
    # authorization: str = Header(None) # MODIFICADO
):
    logger = logging.getLogger("growth_prompt")
    user_id_hash_from_token = current_claims.sub
    
    # NUEVO: Validar que el user_id_hash del query coincide con el del token, o usar solo el del token.
    # Opción 1: Validar coincidencia
    if user_id_hash != user_id_hash_from_token:
        logger.warning(f"Discrepancia de user_id_hash en /growth_prompt. Token: {user_id_hash_from_token}, Query: {user_id_hash}")
        raise HTTPException(status_code=403, detail="User ID en query no coincide con el token.")
    # Opción 2: Usar siempre el del token (más seguro)
    # user_id_to_use = user_id_hash_from_token
    # logger.info(f"Procesando /growth_prompt para usuario (token) {user_id_to_use}, tipo {prompt_type}")

    # La lógica original usa `user_id_hash` del Query. Se mantiene así después de la validación.
    logger.info(f"Procesando /growth_prompt para usuario {user_id_hash} (validado con token), tipo {prompt_type}")

    # if not authorization or not authorization.startswith("Bearer "): # ELIMINADO
    #     raise HTTPException(status_code=403, detail="Token requerido")
    # Verificar cooldown
    last_prompt = await db.execute(select(GrowthLog).filter(
        GrowthLog.user_id_hash == user_id_hash,
        GrowthLog.prompt_type == prompt_type
    ).order_by(desc(GrowthLog.shown_at)))
    last_prompt = last_prompt.scalars().first()
    now = datetime.utcnow()
    cooldown = 0
    if last_prompt and last_prompt.cooldown_until and last_prompt.cooldown_until > now:
        cooldown = int((last_prompt.cooldown_until - now).total_seconds())
        return {"status": "cooldown", "cooldown_seconds": cooldown}
    # Registrar prompt
    cooldown_seconds = 604800 if prompt_type == "PUSH_OPT_IN" else 1209600  # 7d o 14d
    cooldown_until = now + timedelta(seconds=cooldown_seconds)
    log = GrowthLog(
        user_id_hash=user_id_hash,
        prompt_type=prompt_type,
        shown_at=now,
        cooldown_until=cooldown_until
    )
    await db.add(log)
    await db.commit()
    return {"status": "shown", "prompt_type": prompt_type, "cooldown_until": cooldown_until.isoformat()}

@router.get("/leaderboard")
async def leaderboard(
    league_id: str = Query("global_weekly"),
    top_n: int = Query(10),
    current_claims: TokenClaims = Depends(get_current_team_user_claims) # NUEVO: Añadir dependencia
    # authorization: str = Header(None) # MODIFICADO
):
    logger = logging.getLogger("leaderboard") # MODIFICADO logger
    # user_id_hash_from_token = current_claims.sub # No se usa directamente aquí, pero valida el acceso.
    logger.info(f"Solicitud /leaderboard recibida. League: {league_id}, Top N: {top_n}. Token validado para usuario {current_claims.sub}")

    base_league_id_to_query = league_id.replace("_weekly", "")
    
    logger.debug(f"leaderboard_DEBUG: Solicitando leaderboard para base_league_id: '{base_league_id_to_query}', top_n: {top_n}")

    # if not authorization or not authorization.startswith("Bearer "): # ELIMINADO
    #     logger.warning("leaderboard_DEBUG: Token no proporcionado o malformado.")
    #     raise HTTPException(status_code=403, detail="Token requerido")
    
    try:
        logger.debug(f"leaderboard_DEBUG: Llamando a get_leaderboard con base_league_id: '{base_league_id_to_query}', top_n={top_n}")
        board_data = get_leaderboard(base_league_id=base_league_id_to_query, top_n=top_n)
        
        if board_data is None:
            logger.warning(f"leaderboard_DEBUG: get_leaderboard devolvió None para '{base_league_id_to_query}'.")
            return [] 
        
        logger.debug(f"leaderboard_DEBUG: Datos del leaderboard recibidos: {board_data}")
        
        response = [{"user_id_hash": str(uid), "xp": xp} for uid, xp in board_data]
        logger.debug(f"leaderboard_DEBUG: Respuesta formateada: {response}")
        return response
        
    except redis.exceptions.ConnectionError as e:
        logger.error(f"leaderboard_DEBUG: Error de conexión con Redis: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail="Error de conexión con el servicio de leaderboard (Redis)")
    except Exception as e:
        logger.error(f"leaderboard_DEBUG: Error inesperado en el endpoint del leaderboard: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno procesando el leaderboard.")

class NextItemRequest(BaseModel):
    session_id: str

class NextItemResponse(BaseModel):
    next_item_id: str = None
    due: str = None
    difficulty: str = None
    message: str = None

@router.post("/next_item", response_model=NextItemResponse)
async def next_item(
    data: NextItemRequest,
    db: AsyncSession = Depends(get_db),
    current_claims: TokenClaims = Depends(get_current_team_user_claims)
):
    logger = logging.getLogger("next_item")
    user_id_hash = current_claims.sub
    external_user_identifier = current_claims.external_user_identifier # Para Supabase
    logger.info(f"Solicitud /next_item para sesión '{data.session_id}'. Token validado para usuario {user_id_hash} (ext: {external_user_identifier})")

    if not external_user_identifier: # Asegurar que external_user_identifier exista
        logger.error(f"CRÍTICO: No hay external_user_identifier en token para usuario {user_id_hash} en /next_item. Denegando.")
        raise HTTPException(status_code=403, detail="Identificación de usuario externa no disponible para verificar permisos de contenido.")

    session_result = await db.execute(select(LessonSession).filter(LessonSession.id == uuid.UUID(data.session_id)))
    session = session_result.scalars().first()

    if not session or session.user_id_hash != user_id_hash:
        logger.warning(f"Sesión '{data.session_id}' no encontrada o no pertenece al usuario '{user_id_hash}'.")
        raise HTTPException(status_code=404, detail="Sesión no válida o no encontrada.")

    if session.ended_at:
        logger.info(f"Sesión '{data.session_id}' ya ha finalizado. No hay próximo ítem.")
        return NextItemResponse(message="La sesión ya ha finalizado.")
    
    current_item_id_int = None
    if session.current_item_id:
        try:
            current_item_id_int = int(session.current_item_id)
        except ValueError:
            logger.error(f"ID de ítem actual '{session.current_item_id}' en sesión no es un entero válido. No se puede determinar el siguiente ítem secuencial.")
            # Considerar si lanzar error o intentar recuperarse de otra forma

    next_item_id_to_return = None
    due_date_str = None
    difficulty_str = None
    message_str = "No hay más ítems disponibles o con permiso en esta lección."
    
    # 1. Prioridad: Errores pendientes para esta sesión
    error_result = await db.execute(select(LessonError).filter(
        LessonError.session_id == session.id,
        LessonError.resolved.is_(False)
    ).order_by(LessonError.created_at.asc()))
    pending_error = error_result.scalars().first()

    if pending_error and pending_error.item_id:
        try:
            next_item_id_to_return = int(pending_error.item_id)
            message_str = f"Repasando error pendiente del capítulo {next_item_id_to_return}."
            logger.info(f"Próximo ítem es error pendiente: chapter_id {next_item_id_to_return} para sesión '{session.id}'.")
        except ValueError:
            logger.error(f"Error pendiente item_id '{pending_error.item_id}' no es un entero válido.")
            next_item_id_to_return = None # Resetear si el ID no es válido

    # 2. Si no hay errores, verificar SRS para el curso de la sesión
    if not next_item_id_to_return:
        now_for_srs = datetime.now(timezone.utc)
        srs_item_result = await db.execute(select(SpacedRepetition).filter(
            SpacedRepetition.user_id_hash == user_id_hash,
            SpacedRepetition.course == session.course, 
            SpacedRepetition.next_due <= now_for_srs
        ).order_by(SpacedRepetition.next_due.asc()))
        srs_item = srs_item_result.scalars().first()
        
        if srs_item and srs_item.item_id:
            next_item_id_to_return = srs_item.item_id
            due_date_str = srs_item.next_due.isoformat()
            difficulty_str = srs_item.difficulty
            message_str = f"Próximo ítem del Sistema de Repetición Espaciada (SRS): capítulo {next_item_id_to_return}."
            logger.info(f"Próximo ítem es SRS: chapter_id {next_item_id_to_return} (due: {due_date_str}, difficulty: {difficulty_str}) para sesión '{session.id}'.")

    # 3. Si no hay errores ni SRS, tomar el siguiente capítulo secuencial del mismo curso
    if not next_item_id_to_return and current_item_id_int is not None:
        # Buscar el capítulo actual para obtener su curso_id y orden
        current_cap_res = await db.execute(select(Capitulo).filter(Capitulo.id == current_item_id_int))
        current_capitulo_obj = current_cap_res.scalars().first()

        if current_capitulo_obj:
            logger.debug(f"Buscando siguiente capítulo secuencial después de {current_item_id_int} (orden: {current_capitulo_obj.orden}) en curso {current_capitulo_obj.curso_id}.")
            next_cap_res = await db.execute(
                select(Capitulo)
                .filter(Capitulo.curso_id == current_capitulo_obj.curso_id)
                .filter(or_(Capitulo.orden > current_capitulo_obj.orden, 
                           and_(Capitulo.orden == current_capitulo_obj.orden, Capitulo.id > current_item_id_int)))
                .order_by(Capitulo.orden.asc().nulls_last(), Capitulo.id.asc())
                .limit(1)
            )
            next_capitulo_obj_candidate = next_cap_res.scalars().first()
            if next_capitulo_obj_candidate:
                next_item_id_to_return = next_capitulo_obj_candidate.id
                message_str = f"Siguiente capítulo secuencial: {next_item_id_to_return}."
                logger.info(f"Próximo ítem es secuencial: chapter_id {next_item_id_to_return} para sesión '{session.id}'.")
        else:
            logger.warning(f"No se pudo encontrar el objeto Capitulo para current_item_id {current_item_id_int} en sesión '{session.id}'. No se puede determinar el siguiente secuencial.")
    
    # --- INICIO DE CAMBIO: Verificar acceso a next_item_id_to_return ---    
    if next_item_id_to_return:
        try:
            capitulo_verificado_result = await db.execute(select(Capitulo).filter(Capitulo.id == next_item_id_to_return))
            capitulo_verificado = capitulo_verificado_result.scalars().first()

            if not capitulo_verificado:
                logger.warning(f"next_item: El ID de capítulo determinado {next_item_id_to_return} no existe en la BD. Anulando.")
                next_item_id_to_return = None
                message_str = "El próximo ítem determinado no es válido. No hay más ítems."
            else:
                logger.info(f"next_item: Capítulo candidato ID {capitulo_verificado.id} ('{capitulo_verificado.titulo}') seleccionado. Verificando acceso (Supabase) para {external_user_identifier}.")
                await ensure_user_material_access(
                    external_user_identifier=external_user_identifier,
                    misuperprofe_chapter_id=capitulo_verificado.id
                )
                logger.info(f"Acceso CONCEDIDO (Supabase) a capítulo {capitulo_verificado.id} para usuario {external_user_identifier}.")
                # Si ensure_user_material_access no lanza excepción, el acceso está concedido.
                # Actualizar session.current_item_id y message_str ya se maneja abajo.
        except HTTPException as e:
            # Si ensure_user_material_access lanza 403, el acceso es denegado.
            # Anulamos next_item_id_to_return y actualizamos el mensaje.
            if e.status_code == 403:
                logger.warning(f"Acceso DENEGADO (Supabase) al capítulo {next_item_id_to_return} para usuario {external_user_identifier}. Detalle: {e.detail}")
                next_item_id_to_return = None
                message_str = f"Acceso denegado al contenido del próximo capítulo {next_item_id_to_return} (Supabase)."
            else:
                # Si es otra HTTPException, la relanzamos.
                raise
        except Exception as e: # Captura general por si algo más falla
            logger.error(f"Error inesperado verificando acceso para next_item {next_item_id_to_return}: {e}", exc_info=True)
            next_item_id_to_return = None
            message_str = "Error interno verificando acceso al próximo ítem."
    # --- FIN DE CAMBIO ---

    if next_item_id_to_return:
        session.current_item_id = str(next_item_id_to_return) # Actualizar el ítem actual en la sesión
        await db.commit()
        logger.info(f"Sesión '{session.id}' actualizada con current_item_id = {next_item_id_to_return}.")
        return NextItemResponse(
            next_item_id=str(next_item_id_to_return),
            due=due_date_str,
            difficulty=difficulty_str,
            message=message_str
        )
    else:
        logger.info(f"No se encontró próximo ítem para sesión '{session.id}'. Mensaje: {message_str}")
        return NextItemResponse(message=message_str)

@router.get("/analytics/user_dashboard")
async def user_dashboard(
    # user_id_hash: str = Query(...), # MODIFICADO: Se obtiene del token
    course: Optional[str] = Query(None), # MODIFICADO: Hacer opcional y obtenerlo si se proporciona
    db: AsyncSession = Depends(get_db),
    current_claims: TokenClaims = Depends(get_current_team_user_claims) # NUEVO: Añadir dependencia
    # authorization: str = Header(None) # MODIFICADO
):
    logger = logging.getLogger("user_dashboard") # MODIFICADO logger
    user_id_hash_from_token = current_claims.sub
    logger.info(f"Solicitud /analytics/user_dashboard para usuario (token) '{user_id_hash_from_token}'. Course param: '{course}'")

    # if not authorization or not authorization.startswith("Bearer "): # ELIMINADO
    #     logger.warning("user_dashboard_DEBUG: Token no proporcionado o malformado.")
    #     raise HTTPException(status_code=403, detail="Token requerido")
    
    try:
        # Progreso general
        logger.debug(f"user_dashboard: Consultando UserProgress para usuario (token) {user_id_hash_from_token}")
        # La lógica original usaba user_id_hash del query. Ahora se usa el del token.
        progress_result = await db.execute(select(UserProgress).filter(UserProgress.user_id_hash == user_id_hash_from_token))
        progress_list = progress_result.scalars().all()
        logger.debug(f"user_dashboard: UserProgress encontrado: {len(progress_list)} registro(s).")
        if not progress_list:
            logger.warning(f"user_dashboard: No se encontró UserProgress para {user_id_hash_from_token}. Se devolverán valores por defecto para algunas secciones.")

        # Streaks
        logger.debug(f"user_dashboard: Consultando Streak para user_id_hash: {user_id_hash_from_token}")
        streak_result = await db.execute(select(Streak).filter(Streak.user_id_hash == user_id_hash_from_token))
        streak = streak_result.scalars().first()
        logger.debug(f"user_dashboard: Streak encontrado: {bool(streak)}")

        achievements = ""
        if progress_list and hasattr(progress_list[0], "achievements") and progress_list[0].achievements is not None:
            achievements = progress_list[0].achievements
        logger.debug(f"user_dashboard: Achievements procesados: '{achievements[:50]}...' (si es largo)")

        # Errores frecuentes
        logger.debug(f"user_dashboard: Consultando errores frecuentes (SpacedRepetition) para user_id_hash: {user_id_hash_from_token}, curso: {course}")
        
        query_errors = select(SpacedRepetition).filter(SpacedRepetition.user_id_hash == user_id_hash_from_token)
        
        if course:
            logger.debug(f"user_dashboard: Aplicando filtro de curso '{course}' a los errores frecuentes.")
            query_errors = query_errors.filter(SpacedRepetition.course == course)
            
        errors_result = await db.execute(query_errors.order_by(SpacedRepetition.times_incorrect.desc()).limit(5))
        errors_list = errors_result.scalars().all()
        logger.debug(f"user_dashboard: Errores frecuentes encontrados (SpacedRepetition): {len(errors_list)} registro(s) después de aplicar filtros.")
        frequent_errors = [
            {"item_id": str(e.item_id), "course": e.course, "times_incorrect": e.times_incorrect, "difficulty": str(e.difficulty) if e.difficulty is not None else None} 
            for e in errors_list if e.times_incorrect > 0
        ]
        logger.debug(f"user_dashboard: Errores frecuentes procesados: {frequent_errors}")

        # Recomendaciones
        logger.debug(f"user_dashboard: Consultando recomendaciones (SpacedRepetition) para user_id_hash: {user_id_hash_from_token}, curso: {course}")
        
        query_recommendations = select(SpacedRepetition).filter(
            SpacedRepetition.user_id_hash == user_id_hash_from_token,
            # SpacedRepetition.difficulty == "hard" # Considerar si este filtro es el mejor o si se necesitan otros criterios
        )

        if course:
            logger.debug(f"user_dashboard: Aplicando filtro de curso '{course}' a las recomendaciones.")
            query_recommendations = query_recommendations.filter(SpacedRepetition.course == course)
        
        # Ejemplo: Tomar las próximas 3 due, independientemente de la dificultad, o las más difíciles si no hay due.
        # Por ahora, mantendremos una lógica simple: las próximas due, o las más incorrectas/difíciles.
        # Esta lógica puede evolucionar. Para este fix, solo añadimos el filtro de curso.
        # Si se quiere mantener el filtro por dificultad "hard" cuando NO se especifica curso, se necesitaría lógica adicional.
        # Por ahora, si se especifica curso, filtra por curso. Si no, como estaba (pero sin el filtro de "hard" para simplificar el ejemplo de fix).
        # Para ser más precisos con el error original: si el curso está especificado, filtramos por él Y por dificultad "hard".

        if course: # Aplicar filtro de dificultad solo si el curso también está filtrado, o ajustar según se necesite.
            query_recommendations = query_recommendations.filter(SpacedRepetition.difficulty == "hard")
        else:
            # Si no se especifica curso, podríamos querer las recomendaciones "hard" globales, o ninguna.
            # Para este ejemplo, si no hay curso, no aplicaremos filtro de dificultad "hard" para no devolver recomendaciones potencialmente irrelevantes.
            # O, para mantener el comportamiento original si no hay curso:
            query_recommendations = query_recommendations.filter(SpacedRepetition.difficulty == "hard")


        recommendations_result = await db.execute(
            query_recommendations.order_by(SpacedRepetition.next_due.asc()).limit(3)
        )
        
        recommendations_list = recommendations_result.scalars().all()
        logger.debug(f"user_dashboard: Recomendaciones encontradas (SpacedRepetition): {len(recommendations_list)} registro(s) después de aplicar filtros.")
        recs = [
            {"item_id": str(r.item_id), "course": r.course, "next_due": r.next_due.isoformat() if r.next_due else None, "difficulty": r.difficulty} 
            for r in recommendations_list
        ]
        logger.debug(f"user_dashboard: Recomendaciones procesadas: {recs}")

        # Resumen por curso
        logger.debug(f"user_dashboard: Procesando resumen por curso...")
        progress_by_course = [
            {
                "course": p.course,
                "total_xp": p.total_xp,
                "current_streak": p.current_streak,
                "longest_streak": p.longest_streak,
                "hearts": getattr(p, "hearts", None),
                "chests": getattr(p, "chests", None)
            } for p in progress_list
        ]
        logger.debug(f"user_dashboard: Resumen por curso procesado: {progress_by_course}")

        response_payload = {
            "user_id_hash": user_id_hash_from_token,
            "streak": {
                "current_days": streak.current_days if streak else 0,
                "longest_days": streak.longest_days if streak else 0
            },
            "achievements": achievements,
            "frequent_errors": frequent_errors,
            "recommendations": recs,
            "progress_by_course": progress_by_course
        }
        logger.debug(f"user_dashboard: Payload de respuesta final: {response_payload}")
        return response_payload

    except Exception as e:
        logger.error(f"user_dashboard: Error inesperado en user_dashboard: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno procesando el dashboard del usuario.")

@router.get("/analytics/progress_over_time")
async def progress_over_time(
    # user_id_hash: str = Query(...), # MODIFICADO: Se obtiene del token
    course: Optional[str] = Query(None), # MODIFICADO: Hacer opcional
    db: AsyncSession = Depends(get_db),
    current_claims: TokenClaims = Depends(get_current_team_user_claims) # NUEVO: Añadir dependencia
    # authorization: str = Header(None) # MODIFICADO
):
    logger = logging.getLogger("progress_over_time") # MODIFICADO logger
    user_id_hash_from_token = current_claims.sub
    logger.info(f"Solicitud /analytics/progress_over_time para usuario (token) '{user_id_hash_from_token}'. Course param: '{course}'")

    # if not authorization or not authorization.startswith("Bearer "): # ELIMINADO
    #     logger.warning("progress_over_time_DEBUG: Token no proporcionado o malformado.")
    #     raise HTTPException(status_code=403, detail="Token requerido")

    try:
        logger.debug(f"progress_over_time: Consultando LessonSession para usuario (token) {user_id_hash_from_token}")
        
        trunc_day_expr = func.date_trunc('day', LessonSession.started_at)

        stmt_sessions = select(
            trunc_day_expr.label('day'),
            func.sum(LessonSession.lesson_xp).label('xp'),
            func.avg(LessonSession.accuracy).label('accuracy'),
            func.count(LessonSession.id).label('sessions')
        ).filter(LessonSession.user_id_hash == user_id_hash_from_token) # MODIFICADO: Usar user_id_hash_from_token
        stmt_sessions = stmt_sessions.group_by(trunc_day_expr)
        
        session_data_result = await db.execute(stmt_sessions)
        results = session_data_result.all()
        logger.debug(f"progress_over_time: LessonSession query ejecutada. {len(results)} día(s) de actividad encontrados.")
        logger.debug(f"progress_over_time: Resultados crudos de LessonSession: {results}")

        logger.debug(f"progress_over_time: Consultando Streak para user_id_hash: {user_id_hash_from_token}")
        streak_result = await db.execute(select(Streak).filter(Streak.user_id_hash == user_id_hash_from_token))
        current_streak_data = streak_result.scalars().first()
        logger.debug(f"progress_over_time: Streak encontrado: {bool(current_streak_data)}. Datos: {current_streak_data}")

        progress_list = [
            {
                "day": r.day.strftime("%Y-%m-%d") if r.day else None,
                "xp": int(r.xp or 0),
                "accuracy": float(r.accuracy or 0.0),
                "sessions": int(r.sessions or 0)
            } for r in results
        ]
        logger.debug(f"progress_over_time: Datos de progreso procesados: {progress_list}")

        response_payload = {
            "progress": progress_list,
            "streak": {
                "current_days": current_streak_data.current_days if current_streak_data else 0,
                "longest_days": current_streak_data.longest_days if current_streak_data else 0
            }
        }
        logger.debug(f"progress_over_time: Payload de respuesta final: {response_payload}")
        return response_payload

    except Exception as e:
        logger.error(f"progress_over_time: Error inesperado en progress_over_time: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno procesando el progreso a lo largo del tiempo.")

class ClaimAchievementRequest(BaseModel):
    user_id_hash: str
    achievement_type: str
    details: str = None

@router.post("/lesson/claim_achievement")
async def claim_achievement(
    data: ClaimAchievementRequest,
    db: AsyncSession = Depends(get_db),
    current_claims: TokenClaims = Depends(get_current_team_user_claims) # NUEVO: Añadir dependencia
    # authorization: str = Header(None) # MODIFICADO
):
    logger = logging.getLogger("claim_achievement") # NUEVO
    user_id_hash_from_token = current_claims.sub

    # NUEVO: Validar que data.user_id_hash coincide con el token, o usar solo el del token.
    if data.user_id_hash != user_id_hash_from_token:
        logger.warning(f"Discrepancia de user_id_hash en /claim_achievement. Token: {user_id_hash_from_token}, Payload: {data.user_id_hash}")
        raise HTTPException(status_code=403, detail="User ID en payload no coincide con el token.")
    
    logger.info(f"Procesando /claim_achievement para usuario {data.user_id_hash} (validado), tipo {data.achievement_type}")

    # if not authorization or not authorization.startswith("Bearer "): # ELIMINADO
    #     raise HTTPException(status_code=403, detail="Token requerido")
    # Registrar logro
    log = AchievementsLog(
        user_id_hash=data.user_id_hash,
        achievement_type=data.achievement_type,
        details=data.details
    )
    await db.add(log)
    await db.commit()
    return {"status": "ok", "achievement_id": log.id}

class SendGrowthNudgeRequest(BaseModel):
    user_id_hash: str
    prompt_type: str
    channel: str = "push"  # push, email, sms
    message: str = None

@router.post("/lesson/send_growth_nudge")
async def send_growth_nudge(
    data: SendGrowthNudgeRequest,
    db: AsyncSession = Depends(get_db),
    current_claims: TokenClaims = Depends(get_current_team_user_claims) # NUEVO: Añadir dependencia
    # authorization: str = Header(None) # MODIFICADO
):
    logger = logging.getLogger("send_growth_nudge") # NUEVO
    user_id_hash_from_token = current_claims.sub

    # NUEVO: Validar que data.user_id_hash coincide con el token, o usar solo el del token.
    if data.user_id_hash != user_id_hash_from_token:
        logger.warning(f"Discrepancia de user_id_hash en /send_growth_nudge. Token: {user_id_hash_from_token}, Payload: {data.user_id_hash}")
        raise HTTPException(status_code=403, detail="User ID en payload no coincide con el token.")

    logger.info(f"Procesando /send_growth_nudge para usuario {data.user_id_hash} (validado), tipo {data.prompt_type}")
    
    # if not authorization or not authorization.startswith("Bearer "): # ELIMINADO
    #     raise HTTPException(status_code=403, detail="Token requerido")
    # Registrar growth_log
    from datetime import datetime, timedelta
    cooldown_seconds = 604800 if data.prompt_type == "PUSH_OPT_IN" else 1209600
    cooldown_until = datetime.utcnow() + timedelta(seconds=cooldown_seconds)
    log = GrowthLog(
        user_id_hash=data.user_id_hash,
        prompt_type=data.prompt_type,
        shown_at=datetime.utcnow(),
        action="NUDGE_SENT",
        cooldown_until=cooldown_until
    )
    await db.add(log)
    await db.commit()
    # Simular envío (hook)
    return {
        "status": "nudge_sent",
        "user_id_hash": data.user_id_hash,
        "prompt_type": data.prompt_type,
        "channel": data.channel,
        "cooldown_until": cooldown_until.isoformat(),
        "message": data.message or "Nudge enviado (simulado)"
    }

@router.get("/lesson/league_status")
async def league_status(
    user_id_hash: str = Query(...), # Mantener Query param por ahora, pero validar contra token
    league_id: str = Query("default"),
    db: AsyncSession = Depends(get_db), # db no se usa en la lógica original, pero lo dejo por si acaso
    current_claims: TokenClaims = Depends(get_current_team_user_claims) # NUEVO: Añadir dependencia
    # authorization: str = Header(None) # MODIFICADO
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=403, detail="Token requerido")
    # Obtener leaderboard semanal
    board = get_leaderboard(league_id, 100)
    # Buscar posición del usuario
    position = next((i+1 for i, (uid, _) in enumerate(board) if uid == user_id_hash), None)
    # Determinar liga por posición
    if position is None:
        league = "Sin liga"
    elif position <= 10:
        league = "Oro"
    elif position <= 30:
        league = "Plata"
    else:
        league = "Bronce"
    return {
        "user_id_hash": user_id_hash,
        "league": league,
        "position": position,
        "total_users": len(board)
    }

@router.get("/item/{item_id}")
async def get_lesson_item(
    item_id: int = Path(..., description="ID del capítulo o ítem de teoría"),
    db: AsyncSession = Depends(get_db),
    current_claims: TokenClaims = Depends(get_current_team_user_claims)
):
    """Obtiene el contenido de un ítem de lección específico (capítulo) por su ID."""
    logger = logging.getLogger("get_lesson_item")
    user_id_hash = current_claims.sub
    external_user_identifier = current_claims.external_user_identifier
    
    logger.info(f"Petición para obtener ítem de lección ID: {item_id} por usuario {user_id_hash} (ext: {external_user_identifier})")

    # TODO (Supabase): Verificar si external_user_identifier tiene acceso a misuperprofe_chapter_id = item_id
    # Esta verificación debe ocurrir ANTES de devolver el contenido.
    # Si no tiene acceso, lanzar HTTPException(status_code=403, detail="Acceso denegado al contenido de este capítulo.")
    if not external_user_identifier:
        logger.error(f"CRÍTICO: No hay external_user_identifier en token para usuario {user_id_hash} en /item/{item_id}. Denegando.")
        raise HTTPException(status_code=403, detail="Identificación de usuario externa no disponible para verificar permisos de contenido.")

    tiene_acceso_supabase = check_user_material_access_supabase(
        external_user_identifier=external_user_identifier,
        misuperprofe_chapter_id=item_id
    )

    if not tiene_acceso_supabase:
        logger.warning(f"Acceso DENEGADO (Supabase) al capítulo {item_id} para usuario {external_user_identifier}. No se puede obtener el ítem.")
        raise HTTPException(status_code=403, detail=f"No tiene permiso para acceder al contenido del capítulo ID {item_id} (Supabase).")
    logger.info(f"Acceso CONCEDIDO (Supabase) al capítulo {item_id} para usuario {external_user_identifier}.")

    capitulo_result = await db.execute(
        select(Capitulo)
        .options(selectinload(Capitulo.curso))
        .filter(Capitulo.id == item_id)
    )
    capitulo = capitulo_result.scalars().first()

    if not capitulo:
        logger.warning(f"Capítulo con ID {item_id} no encontrado.") # El acceso ya fue verificado, así que esto no debería pasar si el ID es válido
        raise HTTPException(status_code=404, detail="Capítulo no encontrado.")

    return {
        "item_id": capitulo.id,
        "titulo": capitulo.titulo,
        "contenido_html": capitulo.contenido_html,
        "contenido_md": capitulo.contenido_md,
        "curso": capitulo.curso.nombre if capitulo.curso else "N/A",
        "orden": capitulo.orden,
        "beta_difficulty": capitulo.beta_difficulty,
    }

@router.post(
    "/result",
    summary="Registrar el resultado de una evaluación de lección por LLM",
    description="Permite a un cliente (ej. un LLM externo o frontend) registrar el resultado de una pregunta o interacción de evaluación generada y evaluada por un LLM.",
    status_code=201, 
    response_model=None 
)
async def record_llm_lesson_result(
    result_data: LessonResultCreate,
    db: AsyncSession = Depends(get_db),
    current_claims: TokenClaims = Depends(get_current_team_user_claims) # NUEVO: Añadir dependencia
    # authorization: str = Header(None) # MODIFICADO
):
    logger = logging.getLogger("record_llm_lesson_result") # MODIFICADO logger
    user_id_hash_from_token = current_claims.sub
    
    # NUEVO: Validar que result_data.student_id (que es el user_id_hash) coincide con el token.
    if result_data.student_id != user_id_hash_from_token:
        logger.warning(f"Discrepancia de student_id en /result. Token: {user_id_hash_from_token}, Payload: {result_data.student_id}")
        raise HTTPException(status_code=403, detail="Student ID en payload no coincide con el token.")

    logger.info(f"Solicitud para registrar resultado de LLM: student_id={result_data.student_id} (validado), chapter_id={result_data.chapter_id}")

    try:
        # Validar si el chapter_id existe (opcional pero recomendado)
        capitulo_existente = await db.get(Capitulo, result_data.chapter_id)
        if not capitulo_existente:
            logger.warning(f"Intento de registrar resultado para chapter_id inexistente: {result_data.chapter_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Capítulo con ID {result_data.chapter_id} no encontrado."
            )

        nuevo_resultado = Resultado(
            estudiante_id=result_data.student_id,
            capitulo_id=result_data.chapter_id,
            respuesta="L", # Modificado: Usar 'L' para LLM y cumplir String(1)
            es_correcta=result_data.is_correct,
            fecha=datetime.utcnow(), 
            feedback=result_data.llm_feedback,
            pregunta_generada = result_data.llm_question, # Añadido
            respuesta_usuario = result_data.user_response, # Añadido
        )

        db.add(nuevo_resultado)
        await db.commit()
        await db.refresh(nuevo_resultado)

        logger.info(f"Resultado de LLM registrado con ID: {nuevo_resultado.id} para estudiante: {result_data.student_id}, capítulo: {result_data.chapter_id}")

        return {
            "message": "Resultado registrado exitosamente.",
            "result_id": nuevo_resultado.id,
            "student_id": nuevo_resultado.estudiante_id,
            "chapter_id": nuevo_resultado.capitulo_id,
            "is_correct": nuevo_resultado.es_correcta
        }

    except HTTPException:
        # Re-lanzar HTTPExceptions para que FastAPI las maneje
        raise
    except Exception as e:
        logger.error(f"Error al registrar resultado de LLM para estudiante {result_data.student_id}: {e}", exc_info=True)
        await db.rollback() # Asegurar rollback en caso de otros errores
        raise HTTPException(status_code=500, detail="Error interno al registrar el resultado.")

lesson_router = router 

def to_enum_state(val):
    if isinstance(val, str):
        val_lower = val.lower()
        if val_lower == "completado":
            return UserChapterStatus.COMPLETADO
        elif val_lower == "en_progreso":
            return UserChapterStatus.EN_PROGRESO
        elif val_lower == "no_iniciado":
            return UserChapterStatus.NO_INICIADO
        raise ValueError(f"Valor de estado inválido: {val}. Solo se permiten: 'no_iniciado', 'en_progreso', 'completado'.")
    return val 

# --- HOOK DE RASTREO GLOBAL PARA 'COMPLETADO' ---
def log_if_completado(val, contexto):
    if isinstance(val, str) and val.upper() == 'COMPLETADO':
        with open('/tmp/completado_trace.log', 'a') as f:
            f.write(f"[DETECCIÓN] Valor 'COMPLETADO' detectado en contexto: {contexto}\n")
            f.write(f"Stack trace:\n{''.join(inspect.stack()[1].code_context or [''])}\n\n")
    return val 

@router.post(
    "/result",
    summary="Registrar el resultado de una evaluación de lección por LLM",
    description="Permite a un cliente (ej. un LLM externo o frontend) registrar el resultado de una pregunta o interacción de evaluación generada y evaluada por un LLM.",
    status_code=201, 
    response_model=None 
)
async def record_llm_lesson_result(
    result_data: LessonResultCreate,
    db: AsyncSession = Depends(get_db),
    current_claims: TokenClaims = Depends(get_current_team_user_claims) # NUEVO: Añadir dependencia
    # authorization: str = Header(None) # MODIFICADO
):
    logger = logging.getLogger("record_llm_lesson_result") # MODIFICADO logger
    user_id_hash_from_token = current_claims.sub
    
    # NUEVO: Validar que result_data.student_id (que es el user_id_hash) coincide con el token.
    if result_data.student_id != user_id_hash_from_token:
        logger.warning(f"Discrepancia de student_id en /result. Token: {user_id_hash_from_token}, Payload: {result_data.student_id}")
        raise HTTPException(status_code=403, detail="Student ID en payload no coincide con el token.")

    logger.info(f"Solicitud para registrar resultado de LLM: student_id={result_data.student_id} (validado), chapter_id={result_data.chapter_id}")

    try:
        # Validar si el chapter_id existe (opcional pero recomendado)
        capitulo_existente = await db.get(Capitulo, result_data.chapter_id)
        if not capitulo_existente:
            logger.warning(f"Intento de registrar resultado para chapter_id inexistente: {result_data.chapter_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Capítulo con ID {result_data.chapter_id} no encontrado."
            )

        nuevo_resultado = Resultado(
            estudiante_id=result_data.student_id,
            capitulo_id=result_data.chapter_id,
            respuesta="L", # Modificado: Usar 'L' para LLM y cumplir String(1)
            es_correcta=result_data.is_correct,
            fecha=datetime.utcnow(), 
            feedback=result_data.llm_feedback,
            pregunta_generada = result_data.llm_question, # Añadido
            respuesta_usuario = result_data.user_response, # Añadido
        )

        db.add(nuevo_resultado)
        await db.commit()
        await db.refresh(nuevo_resultado)

        logger.info(f"Resultado de LLM registrado con ID: {nuevo_resultado.id} para estudiante: {result_data.student_id}, capítulo: {result_data.chapter_id}")

        return {
            "message": "Resultado registrado exitosamente.",
            "result_id": nuevo_resultado.id,
            "student_id": nuevo_resultado.estudiante_id,
            "chapter_id": nuevo_resultado.capitulo_id,
            "is_correct": nuevo_resultado.es_correcta
        }

    except HTTPException:
        # Re-lanzar HTTPExceptions para que FastAPI las maneje
        raise
    except Exception as e:
        logger.error(f"Error al registrar resultado de LLM para estudiante {result_data.student_id}: {e}", exc_info=True)
        await db.rollback() # Asegurar rollback en caso de otros errores
        raise HTTPException(status_code=500, detail="Error interno al registrar el resultado.")

@router.get("/item/{item_id}")
async def get_lesson_item(
    item_id: int = Path(..., description="ID del capítulo o ítem de teoría"),
    db: AsyncSession = Depends(get_db),
    current_claims: TokenClaims = Depends(get_current_team_user_claims)
):
    """Obtiene el contenido de un ítem de lección específico (capítulo) por su ID."""
    logger = logging.getLogger("get_lesson_item")
    user_id_hash = current_claims.sub
    external_user_identifier = current_claims.external_user_identifier
    
    logger.info(f"Petición para obtener ítem de lección ID: {item_id} por usuario {user_id_hash} (ext: {external_user_identifier})")

    # TODO (Supabase): Verificar si external_user_identifier tiene acceso a misuperprofe_chapter_id = item_id
    # Esta verificación debe ocurrir ANTES de devolver el contenido.
    # Si no tiene acceso, lanzar HTTPException(status_code=403, detail="Acceso denegado al contenido de este capítulo.")
    if not external_user_identifier:
        logger.error(f"CRÍTICO: No hay external_user_identifier en token para usuario {user_id_hash} en /item/{item_id}. Denegando.")
        raise HTTPException(status_code=403, detail="Identificación de usuario externa no disponible para verificar permisos de contenido.")

    tiene_acceso_supabase = check_user_material_access_supabase(
        external_user_identifier=external_user_identifier,
        misuperprofe_chapter_id=item_id
    )

    if not tiene_acceso_supabase:
        logger.warning(f"Acceso DENEGADO (Supabase) al capítulo {item_id} para usuario {external_user_identifier}. No se puede obtener el ítem.")
        raise HTTPException(status_code=403, detail=f"No tiene permiso para acceder al contenido del capítulo ID {item_id} (Supabase).")
    logger.info(f"Acceso CONCEDIDO (Supabase) al capítulo {item_id} para usuario {external_user_identifier}.")

    capitulo_result = await db.execute(
        select(Capitulo)
        .options(selectinload(Capitulo.curso))
        .filter(Capitulo.id == item_id)
    )
    capitulo = capitulo_result.scalars().first()

    if not capitulo:
        logger.warning(f"Capítulo con ID {item_id} no encontrado.") # El acceso ya fue verificado, así que esto no debería pasar si el ID es válido
        raise HTTPException(status_code=404, detail="Capítulo no encontrado.")

    return {
        "item_id": capitulo.id,
        "titulo": capitulo.titulo,
        "contenido_html": capitulo.contenido_html,
        "contenido_md": capitulo.contenido_md,
        "curso": capitulo.curso.nombre if capitulo.curso else "N/A",
        "orden": capitulo.orden,
        "beta_difficulty": capitulo.beta_difficulty,
    }

# Stub temporal para permitir acceso siempre
async def ensure_user_material_access(external_user_identifier, misuperprofe_chapter_id):
    pass