"""
Endpoints para logros y gamificación del usuario.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, ConfigDict
from datetime import datetime, timedelta
import logging
from typing import Optional, List

from app.db.session import get_session
from app.models.adaptive import UserProgress, AchievementsLog, Streak
from app.tools.redis_utils import get_leaderboard, get_user_rank_in_leaderboard
import hashlib

def _generar_user_id_hash(user_id: str) -> str:
    """Genera un hash SHA256 para el user_id."""
    return hashlib.sha256(user_id.encode('utf-8')).hexdigest()

from app.config import settings

router = APIRouter(prefix="/achievements", tags=["achievements"])
logger = logging.getLogger(__name__)

# Modelos Pydantic
class UserAchievementsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    user_id: str
    total_xp: int
    current_streak: int
    longest_streak: int
    achievements: List[str]
    rank: Optional[int]
    level: int

class AchievementRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    user_id: str
    achievement_type: str
    details: Optional[str] = None

class AchievementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    achievement_unlocked: bool
    achievement_name: str
    xp_earned: int
    message: str

def verify_bearer_token(request: Request):
    """Verifica el Bearer token."""
    auth = request.headers.get("Authorization")
    if not auth or auth != f"Bearer {settings.API_KEY}":
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True

@router.get("/user/{user_id}", response_model=UserAchievementsResponse)
async def get_user_achievements(
    user_id: str,
    request: Request,
    db: AsyncSession = Depends(get_session)
):
    """
    Obtiene los logros y estadísticas de un usuario.
    """
    verify_bearer_token(request)
    
    try:
        user_id_hash = _generar_user_id_hash(user_id)
        
        # Obtener progreso del usuario
        progress_result = await db.execute(
            select(UserProgress).filter(UserProgress.user_id_hash == user_id_hash)
        )
        user_progress = progress_result.scalars().all()
        
        # Obtener streak
        streak_result = await db.execute(
            select(Streak).filter(Streak.user_id_hash == user_id_hash)
        )
        user_streak = streak_result.scalars().first()
        
        # Obtener logros
        achievements_result = await db.execute(
            select(AchievementsLog).filter(AchievementsLog.user_id_hash == user_id_hash)
        )
        achievements = achievements_result.scalars().all()
        
        # Calcular total XP
        total_xp = sum(p.total_xp for p in user_progress) if user_progress else 0
        
        # Calcular nivel (cada 100 XP = 1 nivel)
        level = (total_xp // 100) + 1
        
        # Obtener rank en leaderboard
        rank = get_user_rank_in_leaderboard("global_weekly", user_id_hash)
        
        # Lista de logros desbloqueados
        achievement_names = [a.achievement_type for a in achievements]
        
        return UserAchievementsResponse(
            user_id=user_id,
            total_xp=total_xp,
            current_streak=user_streak.current_days if user_streak else 0,
            longest_streak=user_streak.longest_days if user_streak else 0,
            achievements=achievement_names,
            rank=rank,
            level=level
        )
        
    except Exception as e:
        logger.error(f"Error en get_user_achievements: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router.post("/unlock", response_model=AchievementResponse)
async def unlock_achievement(
    data: AchievementRequest,
    request: Request,
    db: AsyncSession = Depends(get_session)
):
    """
    Desbloquea un logro para un usuario.
    """
    verify_bearer_token(request)
    
    try:
        user_id_hash = _generar_user_id_hash(data.user_id)
        
        # Verificar si el logro ya existe
        existing_achievement = await db.execute(
            select(AchievementsLog).filter(
                AchievementsLog.user_id_hash == user_id_hash,
                AchievementsLog.achievement_type == data.achievement_type
            )
        )
        
        if existing_achievement.scalars().first():
            return AchievementResponse(
                achievement_unlocked=False,
                achievement_name=data.achievement_type,
                xp_earned=0,
                message="Logro ya desbloqueado"
            )
        
        # Crear nuevo logro
        new_achievement = AchievementsLog(
            user_id_hash=user_id_hash,
            achievement_type=data.achievement_type,
            details=data.details,
            unlocked_at=datetime.utcnow()
        )
        db.add(new_achievement)
        
        # Calcular XP del logro
        xp_earned = calculate_achievement_xp(data.achievement_type)
        
        # Actualizar progreso del usuario
        await update_user_progress(db, user_id_hash, xp_earned)
        
        await db.commit()
        
        return AchievementResponse(
            achievement_unlocked=True,
            achievement_name=data.achievement_type,
            xp_earned=xp_earned,
            message=f"¡Logro desbloqueado! +{xp_earned} XP"
        )
        
    except Exception as e:
        logger.error(f"Error en unlock_achievement: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router.get("/leaderboard")
async def get_achievements_leaderboard(
    league_id: str = Query("global_weekly"),
    top_n: int = Query(10),
    request: Request = None
):
    """
    Obtiene el leaderboard de XP.
    """
    verify_bearer_token(request)
    
    try:
        leaderboard = get_leaderboard(league_id, top_n)
        return {
            "league_id": league_id,
            "top_n": top_n,
            "leaderboard": leaderboard
        }
        
    except Exception as e:
        logger.error(f"Error en get_achievements_leaderboard: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

def calculate_achievement_xp(achievement_type: str) -> int:
    """Calcula el XP que otorga cada tipo de logro."""
    xp_map = {
        "first_correct": 10,
        "streak_3": 20,
        "streak_7": 50,
        "streak_30": 100,
        "course_complete": 200,
        "perfect_score": 100,
        "early_bird": 15,
        "night_owl": 15,
        "weekend_warrior": 25,
        "social_learner": 30,
        "helpful": 20,
        "consistent": 40
    }
    return xp_map.get(achievement_type, 10)

async def update_user_progress(db: AsyncSession, user_id_hash: str, xp_earned: int):
    """Actualiza el progreso del usuario con XP ganado."""
    # Buscar progreso existente o crear uno nuevo
    progress_result = await db.execute(
        select(UserProgress).filter(
            UserProgress.user_id_hash == user_id_hash,
            UserProgress.course == "general"  # Progreso general
        )
    )
    user_progress = progress_result.scalars().first()
    
    if user_progress:
        user_progress.total_xp += xp_earned
        user_progress.last_active = datetime.utcnow()
    else:
        new_progress = UserProgress(
            user_id_hash=user_id_hash,
            course="general",
            total_xp=xp_earned,
            last_active=datetime.utcnow()
        )
        db.add(new_progress)

@router.get("/check_achievements/{user_id}")
async def check_achievements(
    user_id: str,
    request: Request,
    db: AsyncSession = Depends(get_session)
):
    """
    Verifica si el usuario ha desbloqueado nuevos logros.
    """
    verify_bearer_token(request)
    
    try:
        user_id_hash = _generar_user_id_hash(user_id)
        
        # Obtener estadísticas del usuario
        from app.api.log import user_stats
        stats_response = await user_stats(request, user_id, db)
        
        # Verificar logros basados en estadísticas
        unlocked_achievements = []
        
        # Logro: Primera respuesta correcta
        if stats_response.get("total_attempts", 0) == 1 and stats_response.get("correct_attempts", 0) == 1:
            achievement_data = AchievementRequest(
                user_id=user_id,
                achievement_type="first_correct"
            )
            # Intentar desbloquear
            try:
                await unlock_achievement(achievement_data, request, db)
                unlocked_achievements.append("first_correct")
            except:
                pass
        
        # Logro: Streak de 3 días
        # Logro: Streak de 7 días
        # Logro: Streak de 30 días
        # Logro: Curso completado
        # Logro: Puntuación perfecta
        # etc.
        
        return {
            "user_id": user_id,
            "unlocked_achievements": unlocked_achievements,
            "message": f"Se verificaron {len(unlocked_achievements)} nuevos logros"
        }
        
    except Exception as e:
        logger.error(f"Error en check_achievements: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}") 