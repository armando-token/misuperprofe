from fastapi import APIRouter, Request, HTTPException, status, Depends, Query
from pydantic import BaseModel
import os
import asyncpg
from datetime import datetime
import random
from sqlalchemy import select, func
from ..models.capitulo import Capitulo
from ..models.curso import Curso
from ..db.session import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from rapidfuzz import process, fuzz
import traceback
import hashlib
from ..tools.redis_utils import add_xp_leaderboard

log_router = APIRouter()

API_KEY = os.getenv("API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL_ASYNCPG")

print(f"[DEBUG] API_KEY cargada en backend: {API_KEY}")

class LogResultRequest(BaseModel):
    user_id: str
    question_id: str
    answer: str
    is_correct: bool
    course: str
    topic: str

def generar_user_id_hash(email: str) -> str:
    return hashlib.sha256(email.lower().encode('utf-8')).hexdigest()

@log_router.post("/log_result")
async def log_result(request: Request, data: LogResultRequest):
    auth = request.headers.get("Authorization")
    if not auth or auth != f"Bearer {API_KEY}":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    user_id_hash = generar_user_id_hash(data.user_id)
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute(
        """
        INSERT INTO attempts (user_id_hash, question_id, answer, is_correct, course, topic)
        VALUES ($1, $2, $3, $4, $5, $6)
        """,
        user_id_hash, data.question_id, data.answer, data.is_correct, data.course, data.topic
    )
    await conn.close()
    # Si la respuesta es correcta, sumar 1 XP al leaderboard semanal
    if data.is_correct:
        add_xp_leaderboard("global_weekly", user_id_hash, 1)
    return {"status": "ok"}

@log_router.get("/user_stats")
async def user_stats(request: Request, user_id: str = Query(...), desde: str = Query(None), hasta: str = Query(None)):
    auth = request.headers.get("Authorization")
    if not auth or auth != f"Bearer {API_KEY}":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    try:
        user_id_hash = generar_user_id_hash(user_id)
        conn = await asyncpg.connect(DATABASE_URL)
        filtros = ["user_id_hash = $1"]
        params = [user_id_hash]
        idx = 2
        if desde:
            filtros.append(f"fecha >= ${idx}")
            params.append(desde)
            idx += 1
        if hasta:
            filtros.append(f"fecha <= ${idx}")
            params.append(hasta)
            idx += 1
        filtro_sql = " AND ".join(filtros)
        # Resumen por curso y tema
        resumen = await conn.fetch(f'''
            SELECT course, topic,
                   COUNT(*) as total_intentos,
                   SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as aciertos,
                   SUM(CASE WHEN NOT is_correct THEN 1 ELSE 0 END) as errores
            FROM attempts
            WHERE {filtro_sql}
            GROUP BY course, topic
        ''', *params)
        # Agrupar por curso
        cursos = {}
        for row in resumen:
            curso = row["course"]
            if curso not in cursos:
                cursos[curso] = {"curso": curso, "total_intentos": 0, "aciertos": 0, "errores": 0, "temas": []}
            cursos[curso]["total_intentos"] += row["total_intentos"]
            cursos[curso]["aciertos"] += row["aciertos"]
            cursos[curso]["errores"] += row["errores"]
            cursos[curso]["temas"].append({
                "tema": row["topic"],
                "total_intentos": row["total_intentos"],
                "aciertos": row["aciertos"],
                "errores": row["errores"],
                "porcentaje_acierto": float(row["aciertos"]) / row["total_intentos"] * 100 if row["total_intentos"] > 0 else 0.0
            })
        for c in cursos.values():
            c["porcentaje_acierto"] = float(c["aciertos"]) / c["total_intentos"] * 100 if c["total_intentos"] > 0 else 0.0
        # Últimos 10 intentos
        ultimos = await conn.fetch(f'''
            SELECT fecha, course, topic, question_id, answer, is_correct
            FROM attempts
            WHERE {filtro_sql}
            ORDER BY fecha DESC
            LIMIT 10
        ''', *params)
        await conn.close()
        return {
            "user_id": user_id,
            "resumen_por_curso": list(cursos.values()),
            "ultimos_intentos": [dict(u) for u in ultimos]
        }
    except Exception as e:
        print("[ERROR][user_stats]", traceback.format_exc())
        raise HTTPException(status_code=500, detail="Error interno en el backend.")

@log_router.get("/recomendar_plan_estudio")
async def recomendar_plan_estudio(request: Request, user_id: str = Query(...)):
    auth = request.headers.get("Authorization")
    if not auth or auth != f"Bearer {API_KEY}":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    conn = await asyncpg.connect(DATABASE_URL)
    resumen = await conn.fetch('''
        SELECT course, topic,
               COUNT(*) as total_intentos,
               SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as aciertos,
               SUM(CASE WHEN NOT is_correct THEN 1 ELSE 0 END) as errores
        FROM attempts
        WHERE user_id_hash = $1
        GROUP BY course, topic
    ''', user_id)
    await conn.close()
    recomendaciones = []
    for row in resumen:
        total = row["total_intentos"]
        aciertos = row["aciertos"]
        errores = row["errores"]
        porcentaje = float(aciertos) / total * 100 if total > 0 else 0.0
        recomendaciones.append({
            "curso": row["course"],
            "tema": row["topic"],
            "total_intentos": total,
            "aciertos": aciertos,
            "errores": errores,
            "porcentaje_acierto": porcentaje
        })
    # Ordenar por menor porcentaje de acierto y más errores
    recomendaciones.sort(key=lambda x: (x["porcentaje_acierto"], -x["errores"]))
    # Devolver los 5 temas más críticos
    return {"user_id": user_id, "recomendaciones": recomendaciones[:5]}

@log_router.get("/get_question")
async def get_question(request: Request, course: str = Query(None), topic: str = Query(None)):
    auth = request.headers.get("Authorization")
    if not auth or auth != f"Bearer {API_KEY}":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    if not course:
        raise HTTPException(status_code=400, detail="Debes especificar el curso.")

    async for session in get_session():
        # Obtener todos los cursos
        cursos_result = await session.execute(select(Curso))
        cursos = cursos_result.scalars().all()
        cursos_nombres = [c.nombre for c in cursos]
        # Buscar el curso más parecido usando fuzzy matching
        match_curso, score, idx = process.extractOne(
            course,
            cursos_nombres,
            scorer=fuzz.WRatio,
            score_cutoff=70
        ) or (None, 0, None)
        if not match_curso:
            raise HTTPException(status_code=404, detail=f"No se encontró ningún curso similar a '{course}'")
        curso_obj = next(c for c in cursos if c.nombre == match_curso)
        # Buscar capítulos del curso
        capitulos_result = await session.execute(select(Capitulo).where(Capitulo.curso_id == curso_obj.id))
        capitulos = capitulos_result.scalars().all()
        if topic:
            capitulos_titulos = [c.titulo for c in capitulos]
            match_tema, score_tema, idx_tema = process.extractOne(
                topic,
                capitulos_titulos,
                scorer=fuzz.WRatio,
                score_cutoff=60
            ) or (None, 0, None)
            if match_tema:
                capitulos = [c for c in capitulos if c.titulo == match_tema]
        if not capitulos:
            fallback_query = select(Capitulo).limit(1)
            fallback_result = await session.execute(fallback_query)
            capitulos = fallback_result.scalars().all()
            if not capitulos:
                raise HTTPException(status_code=404, detail=f"No se encontró teoría para el curso '{course}'")
        capitulo = random.choice(capitulos)
        question_id = f"gen_{capitulo.id}_{random.randint(1000, 9999)}"
        return {
            "course": match_curso,
            "topic": topic or capitulo.titulo,
            "question_id": question_id,
            "source_chapter": capitulo.titulo,
            "theory_content": capitulo.contenido_html[:500],
            "instruction": "generate_question_from_theory",
            "metadata": {
                "chapter_id": capitulo.id,
                "full_content_available": True
            }
        } 