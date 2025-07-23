#!/usr/bin/env python3
"""
Script para sincronizar XP desde los intentos correctos hacia user_progress.
Este script resuelve el problema de que el XP no se está calculando correctamente.
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.db.session import get_session
from app.models.adaptive import UserProgress
from app.api.log import generar_user_id_hash
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def sync_xp_from_attempts():
    """Sincroniza XP desde los intentos correctos hacia user_progress."""
    
    async for session in get_session():
        try:
            # Obtener todos los intentos agrupados por usuario
            result = await session.execute(text("""
                SELECT 
                    user_id_hash,
                    COUNT(*) as total_attempts,
                    SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as correct_attempts
                FROM attempts 
                GROUP BY user_id_hash
            """))
            
            users_data = result.fetchall()
            logger.info(f"Encontrados {len(users_data)} usuarios con intentos")
            
            for user_data in users_data:
                user_id_hash = user_data.user_id_hash
                total_attempts = user_data.total_attempts
                correct_attempts = user_data.correct_attempts
                
                # Calcular XP (1 XP por respuesta correcta)
                total_xp = correct_attempts
                
                logger.info(f"Usuario {user_id_hash}: {correct_attempts}/{total_attempts} correctos = {total_xp} XP")
                
                # Buscar progreso existente o crear uno nuevo
                progress_result = await session.execute(
                    select(UserProgress).filter(
                        UserProgress.user_id_hash == user_id_hash,
                        UserProgress.course == "general"
                    )
                )
                user_progress = progress_result.scalars().first()
                
                if user_progress:
                    # Actualizar XP existente
                    old_xp = user_progress.total_xp
                    user_progress.total_xp = total_xp
                    user_progress.last_active = datetime.utcnow()
                    logger.info(f"Actualizado XP: {old_xp} -> {total_xp}")
                else:
                    # Crear nuevo progreso
                    new_progress = UserProgress(
                        user_id_hash=user_id_hash,
                        course="general",
                        total_xp=total_xp,
                        last_active=datetime.utcnow()
                    )
                    session.add(new_progress)
                    logger.info(f"Creado nuevo progreso con {total_xp} XP")
            
            await session.commit()
            logger.info("✅ Sincronización de XP completada exitosamente")
            
        except Exception as e:
            logger.error(f"Error en sincronización: {e}")
            await session.rollback()
            raise

async def main():
    """Función principal."""
    logger.info("🔄 Iniciando sincronización de XP desde intentos...")
    await sync_xp_from_attempts()
    logger.info("✅ Sincronización completada")

if __name__ == "__main__":
    asyncio.run(main()) 