"""API de Analytics Avanzados para Administradores."""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, func
from datetime import datetime, timedelta
import json

from app.db.session import get_session
from app.core.mcp import mcp

analytics_router = APIRouter()

@analytics_router.get("/analytics/overview")
async def get_analytics_overview(
    db: AsyncSession = Depends(get_session),
    days: int = Query(default=30, description="Días para analizar")
) -> Dict[str, Any]:
    """Obtiene resumen general de analytics del sistema.
    
    Args:
        db: Sesión de base de datos
        days: Número de días para analizar
        
    Returns:
        Dict con métricas generales del sistema
    """
    try:
        # Fecha límite
        fecha_limite = datetime.utcnow() - timedelta(days=days)
        
        # Consulta de métricas generales
        query = text("""
        SELECT 
            COUNT(DISTINCT r.estudiante_id) as usuarios_activos,
            COUNT(*) as total_intentos,
            SUM(CASE WHEN r.es_correcta THEN 1 ELSE 0 END) as aciertos,
            AVG(CASE WHEN r.es_correcta THEN 1.0 ELSE 0.0 END) * 100 as porcentaje_acierto_global,
            COUNT(DISTINCT c.curso_id) as cursos_utilizados
        FROM resultado r
        JOIN capitulo c ON r.capitulo_id = c.id
        WHERE r.fecha >= :fecha_limite
        """)
        
        result = await db.execute(query, {"fecha_limite": fecha_limite})
        row = result.fetchone()
        
        # Consulta de actividad por día
        query_daily = text("""
        SELECT 
            DATE(r.fecha) as fecha,
            COUNT(*) as intentos,
            COUNT(DISTINCT r.estudiante_id) as usuarios
        FROM resultado r
        WHERE r.fecha >= :fecha_limite
        GROUP BY DATE(r.fecha)
        ORDER BY fecha DESC
        LIMIT 30
        """)
        
        result_daily = await db.execute(query_daily, {"fecha_limite": fecha_limite})
        actividad_diaria = [
            {
                "fecha": str(row.fecha),
                "intentos": row.intentos,
                "usuarios": row.usuarios
            }
            for row in result_daily.fetchall()
        ]
        
        return {
            "periodo_dias": days,
            "usuarios_activos": row.usuarios_activos or 0,
            "total_intentos": row.total_intentos or 0,
            "aciertos": row.aciertos or 0,
            "porcentaje_acierto_global": round(row.porcentaje_acierto_global or 0, 2),
            "cursos_utilizados": row.cursos_utilizados or 0,
            "actividad_diaria": actividad_diaria
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener analytics: {str(e)}"
        )

@analytics_router.get("/analytics/course_performance")
async def get_course_performance(
    db: AsyncSession = Depends(get_session),
    days: int = Query(default=30, description="Días para analizar")
) -> Dict[str, Any]:
    """Obtiene rendimiento por curso.
    
    Args:
        db: Sesión de base de datos
        days: Número de días para analizar
        
    Returns:
        Dict con rendimiento por curso
    """
    try:
        fecha_limite = datetime.utcnow() - timedelta(days=days)
        
        query = text("""
        SELECT 
            cur.nombre as curso,
            COUNT(*) as total_intentos,
            SUM(CASE WHEN r.es_correcta THEN 1 ELSE 0 END) as aciertos,
            COUNT(DISTINCT r.estudiante_id) as usuarios_unicos,
            AVG(CASE WHEN r.es_correcta THEN 1.0 ELSE 0.0 END) * 100 as porcentaje_acierto
        FROM resultado r
        JOIN capitulo c ON r.capitulo_id = c.id
        JOIN curso cur ON c.curso_id = cur.id
        WHERE r.fecha >= :fecha_limite
        GROUP BY cur.nombre, cur.id
        ORDER BY total_intentos DESC
        """)
        
        result = await db.execute(query, {"fecha_limite": fecha_limite})
        cursos = []
        
        for row in result.fetchall():
            cursos.append({
                "curso": row.curso,
                "total_intentos": row.total_intentos,
                "aciertos": row.aciertos,
                "usuarios_unicos": row.usuarios_unicos,
                "porcentaje_acierto": round(row.porcentaje_acierto or 0, 2)
            })
        
        return {
            "periodo_dias": days,
            "cursos": cursos,
            "total_cursos": len(cursos)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener rendimiento por curso: {str(e)}"
        )

@analytics_router.get("/analytics/user_activity")
async def get_user_activity(
    db: AsyncSession = Depends(get_session),
    days: int = Query(default=30, description="Días para analizar"),
    limit: int = Query(default=20, description="Número de usuarios a mostrar")
) -> Dict[str, Any]:
    """Obtiene actividad de usuarios más activos.
    
    Args:
        db: Sesión de base de datos
        days: Número de días para analizar
        limit: Número de usuarios a mostrar
        
    Returns:
        Dict con actividad de usuarios
    """
    try:
        fecha_limite = datetime.utcnow() - timedelta(days=days)
        
        query = text("""
        SELECT 
            r.estudiante_id as usuario,
            COUNT(*) as total_intentos,
            SUM(CASE WHEN r.es_correcta THEN 1 ELSE 0 END) as aciertos,
            AVG(CASE WHEN r.es_correcta THEN 1.0 ELSE 0.0 END) * 100 as porcentaje_acierto,
            MAX(r.fecha) as ultima_actividad
        FROM resultado r
        WHERE r.fecha >= :fecha_limite
        GROUP BY r.estudiante_id
        ORDER BY total_intentos DESC
        LIMIT :limit
        """)
        
        result = await db.execute(query, {
            "fecha_limite": fecha_limite,
            "limit": limit
        })
        
        usuarios = []
        for row in result.fetchall():
            usuarios.append({
                "usuario": row.usuario,
                "total_intentos": row.total_intentos,
                "aciertos": row.aciertos,
                "porcentaje_acierto": round(row.porcentaje_acierto or 0, 2),
                "ultima_actividad": str(row.ultima_actividad)
            })
        
        return {
            "periodo_dias": days,
            "usuarios": usuarios,
            "total_usuarios": len(usuarios)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener actividad de usuarios: {str(e)}"
        )

@analytics_router.get("/analytics/system_health")
async def get_system_health(
    db: AsyncSession = Depends(get_session)
) -> Dict[str, Any]:
    """Obtiene métricas de salud del sistema.
    
    Args:
        db: Sesión de base de datos
        
    Returns:
        Dict con métricas de salud del sistema
    """
    try:
        # Consulta de estadísticas generales
        query_stats = text("""
        SELECT 
            COUNT(*) as total_resultados,
            COUNT(DISTINCT estudiante_id) as total_usuarios,
            COUNT(DISTINCT capitulo_id) as total_capitulos_utilizados,
            MIN(fecha) as fecha_primera_actividad,
            MAX(fecha) as fecha_ultima_actividad
        FROM resultado
        """)
        
        result_stats = await db.execute(query_stats)
        stats = result_stats.fetchone()
        
        # Consulta de capítulos disponibles
        query_chapters = text("""
        SELECT COUNT(*) as total_capitulos
        FROM capitulo
        """)
        
        result_chapters = await db.execute(query_chapters)
        total_capitulos = result_chapters.fetchone().total_capitulos
        
        # Consulta de cursos disponibles
        query_courses = text("""
        SELECT COUNT(*) as total_cursos
        FROM curso
        """)
        
        result_courses = await db.execute(query_courses)
        total_cursos = result_courses.fetchone().total_cursos
        
        return {
            "total_resultados": stats.total_resultados or 0,
            "total_usuarios": stats.total_usuarios or 0,
            "total_capitulos_utilizados": stats.total_capitulos_utilizados or 0,
            "total_capitulos_disponibles": total_capitulos,
            "total_cursos_disponibles": total_cursos,
            "fecha_primera_actividad": str(stats.fecha_primera_actividad) if stats.fecha_primera_actividad else None,
            "fecha_ultima_actividad": str(stats.fecha_ultima_actividad) if stats.fecha_ultima_actividad else None,
            "porcentaje_capitulos_utilizados": round((stats.total_capitulos_utilizados or 0) / total_capitulos * 100, 2) if total_capitulos > 0 else 0
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener salud del sistema: {str(e)}"
        ) 