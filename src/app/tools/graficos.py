"""Tool MCP para generar gráficos de métricas."""

import os
from typing import Dict, Any
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import numpy as np

from app.db.session import get_session
from app.resources.metricas import obtener_metricas_por_materia
from app.core.mcp import mcp
from sqlalchemy import text

# Configuración de estilo
sns.set_theme()

@mcp.tool()
async def generar_grafico_metricas(
    user_id: str,
    tipo: str = "barras",
    db: AsyncSession = Depends(get_session)
) -> Dict[str, Any]:
    """Genera un gráfico de métricas del usuario.
    
    Args:
        user_id: ID del usuario (email)
        tipo: Tipo de gráfico ("barras" o "radar")
        db: Sesión de base de datos asíncrona
        
    Returns:
        Dict con:
            - url: URL del gráfico generado
            - tipo: Tipo de gráfico generado
    """
    try:
        # Obtener datos del usuario desde la tabla resultado
        query = text("""
        SELECT 
            cur.nombre as materia,
            COUNT(*) as total_intentos,
            SUM(CASE WHEN r.es_correcta THEN 1 ELSE 0 END) as aciertos,
            SUM(CASE WHEN NOT r.es_correcta THEN 1 ELSE 0 END) as errores
        FROM resultado r
        JOIN capitulo c ON r.capitulo_id = c.id
        JOIN curso cur ON c.curso_id = cur.id
        WHERE r.estudiante_id = :user_id
        GROUP BY cur.nombre
        """)
        
        result = await db.execute(query, {"user_id": user_id})
        metricas = result.fetchall()
        
        if not metricas:
            return {
                "url": None,
                "tipo": tipo,
                "mensaje": "No hay datos de rendimiento disponibles para este usuario"
            }
            
        # Preparar datos
        cursos = [row.materia for row in metricas]
        porcentajes = []
        
        for row in metricas:
            total = row.total_intentos
            aciertos = row.aciertos
            porcentaje = (aciertos / total * 100) if total > 0 else 0
            porcentajes.append(porcentaje)
        
        # Crear figura
        plt.figure(figsize=(10, 6))
        
        if tipo == "barras":
            # Gráfico de barras
            plt.bar(cursos, porcentajes)
            plt.ylim(0, 100)
            plt.ylabel("Porcentaje de respuestas correctas")
            
        elif tipo == "radar":
            # Gráfico de radar
            angles = np.linspace(0, 2*np.pi, len(cursos), endpoint=False)
            porcentajes = np.array(porcentajes)
            
            # Cerrar el polígono
            porcentajes = np.concatenate((porcentajes, [porcentajes[0]]))
            angles = np.concatenate((angles, [angles[0]]))
            cursos = cursos + [cursos[0]]
            
            ax = plt.subplot(111, projection='polar')
            ax.plot(angles, porcentajes)
            ax.fill(angles, porcentajes, alpha=0.25)
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(cursos[:-1])
            ax.set_ylim(0, 100)
            
        else:
            raise HTTPException(
                status_code=400,
                detail="Tipo de gráfico no válido"
            )
            
        plt.title(f"Rendimiento por materia - Usuario {user_id}")
        
        # Guardar gráfico
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"usuario_{user_id.replace('@', '_at_')}_{tipo}_{timestamp}.png"
        filepath = os.path.join("static/charts", filename)
        plt.savefig(filepath)
        plt.close()
        
        return {
            "url": f"/static/charts/{filename}",
            "tipo": tipo
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al generar gráfico: {str(e)}"
        ) 