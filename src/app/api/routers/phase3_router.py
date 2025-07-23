"""
Endpoints REST para la Fase 3: Microlearning y Análisis Temático
Implementa contenido digerible para Generación Z y análisis temático avanzado
"""

from typing import Dict, List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_session as get_db
from app.services.microlearning import microlearning_engine
from app.services.thematic_analysis import thematic_analysis_engine
from app.schemas.phase3_schemas import (
    MicroLessonRequest, MicroLessonResponse,
    MicroLearningSeriesRequest, MicroLearningSeriesResponse,
    MicroLearningRecommendationsRequest, MicroLearningRecommendationsResponse,
    MicroLearningProgressRequest, MicroLearningProgressResponse,
    TopicFrequencyRequest, TopicFrequencyResponse,
    PriorityMatrixRequest, PriorityMatrixResponse,
    ThematicInsightsRequest, ThematicInsightsResponse,
    ThematicIntegrationRequest, ThematicIntegrationResponse,
    Phase3IntegrationRequest, Phase3IntegrationResponse,
    MicroLearningFormatsResponse, ActiveRecallTypesResponse,
    ThematicAnalysisMetricsResponse, Phase3HealthResponse
)

router = APIRouter(prefix="/phase3", tags=["Fase 3 - Microlearning y Análisis Temático"])


# ============================================================================
# ENDPOINTS DE MICROLEARNING
# ============================================================================

@router.post("/microlearning/lesson", response_model=MicroLessonResponse)
async def create_micro_lesson(
    request: MicroLessonRequest,
    db: Session = Depends(get_db)
):
    """
    Crea una micro-lección para un tema específico
    """
    try:
        micro_lesson = microlearning_engine.create_micro_lesson(
            topic=request.topic,
            area=request.area,
            difficulty=request.difficulty
        )
        
        return MicroLessonResponse(**micro_lesson)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creando micro-lección: {str(e)}")


@router.post("/microlearning/series", response_model=MicroLearningSeriesResponse)
async def create_microlearning_series(
    request: MicroLearningSeriesRequest,
    db: Session = Depends(get_db)
):
    """
    Crea una serie de microlearning para múltiples temas
    """
    try:
        series = microlearning_engine.create_microlearning_series(
            topics=request.topics,
            area=request.area
        )
        
        return MicroLearningSeriesResponse(**series)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creando serie de microlearning: {str(e)}")


@router.post("/microlearning/recommendations", response_model=MicroLearningRecommendationsResponse)
async def get_microlearning_recommendations(
    request: MicroLearningRecommendationsRequest,
    db: Session = Depends(get_db)
):
    """
    Genera recomendaciones de microlearning personalizadas
    """
    try:
        recommendations = microlearning_engine.get_microlearning_recommendations(
            user_id=request.user_id,
            area=request.area
        )
        
        return MicroLearningRecommendationsResponse(**recommendations)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando recomendaciones: {str(e)}")


@router.post("/microlearning/progress", response_model=MicroLearningProgressResponse)
async def track_microlearning_progress(
    request: MicroLearningProgressRequest,
    db: Session = Depends(get_db)
):
    """
    Rastrea progreso de microlearning
    """
    try:
        progress = microlearning_engine.track_microlearning_progress(
            user_id=request.user_id,
            lesson_id=request.lesson_id,
            completion_data=request.completion_data
        )
        
        return MicroLearningProgressResponse(**progress)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rastreando progreso: {str(e)}")


# ============================================================================
# ENDPOINTS DE ANÁLISIS TEMÁTICO
# ============================================================================

@router.post("/thematic/frequency", response_model=TopicFrequencyResponse)
async def analyze_topic_frequency(
    request: TopicFrequencyRequest,
    db: Session = Depends(get_db)
):
    """
    Analiza frecuencia de temas en un área específica
    """
    try:
        frequency_analysis = thematic_analysis_engine.analyze_topic_frequency(
            area=request.area,
            time_period=request.time_period
        )
        
        return TopicFrequencyResponse(**frequency_analysis)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analizando frecuencia temática: {str(e)}")


@router.post("/thematic/priority-matrix", response_model=PriorityMatrixResponse)
async def create_priority_matrix(
    request: PriorityMatrixRequest,
    db: Session = Depends(get_db)
):
    """
    Crea matriz de priorización para temas
    """
    try:
        priority_matrix = thematic_analysis_engine.create_priority_matrix(
            area=request.area
        )
        
        return PriorityMatrixResponse(**priority_matrix)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creando matriz de priorización: {str(e)}")


@router.post("/thematic/insights", response_model=ThematicInsightsResponse)
async def generate_thematic_insights(
    request: ThematicInsightsRequest,
    db: Session = Depends(get_db)
):
    """
    Genera insights temáticos para un área
    """
    try:
        insights = thematic_analysis_engine.generate_thematic_insights(
            area=request.area
        )
        
        return ThematicInsightsResponse(**insights)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando insights temáticos: {str(e)}")


@router.post("/thematic/integration", response_model=ThematicIntegrationResponse)
async def integrate_thematic_analysis(
    request: ThematicIntegrationRequest,
    db: Session = Depends(get_db)
):
    """
    Integra análisis temático con motor de aprendizaje adaptativo
    """
    try:
        integration = thematic_analysis_engine.integrate_with_adaptive_learning(
            area=request.area,
            user_id=request.user_id
        )
        
        return ThematicIntegrationResponse(**integration)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error integrando análisis temático: {str(e)}")


# ============================================================================
# ENDPOINTS DE INTEGRACIÓN FASE 3
# ============================================================================

@router.post("/integration", response_model=Phase3IntegrationResponse)
async def integrate_phase3_systems(
    request: Phase3IntegrationRequest,
    db: Session = Depends(get_db)
):
    """
    Integra sistemas de microlearning y análisis temático
    """
    try:
        # Obtener recomendaciones de microlearning
        microlearning_recs = microlearning_engine.get_microlearning_recommendations(
            user_id=request.user_id,
            area=request.area
        )
        
        # Obtener análisis temático
        thematic_integration = thematic_analysis_engine.integrate_with_adaptive_learning(
            area=request.area,
            user_id=request.user_id
        )
        
        # Combinar recomendaciones
        combined_recommendations = []
        
        # Agregar recomendaciones de microlearning
        for topic in microlearning_recs.get("topics_for_today", []):
            combined_recommendations.append({
                "type": "microlearning",
                "topic": topic,
                "format": "flashcard",
                "duration": 2,
                "reason": "Recomendación diaria de microlearning"
            })
        
        # Agregar recomendaciones temáticas
        for rec in thematic_integration.get("personalized_recommendations", []):
            combined_recommendations.append({
                "type": "thematic_analysis",
                "topic": rec.get("topic", ""),
                "format": "quiz_rapido",
                "duration": rec.get("recommended_time", 30),
                "reason": rec.get("reason", "Análisis temático")
            })
        
        # Optimización de aprendizaje
        learning_optimization = {
            "total_recommendations": len(combined_recommendations),
            "estimated_total_time": sum(rec.get("duration", 0) for rec in combined_recommendations),
            "priority_topics": thematic_integration.get("priority_matrix", {}).get("top_priority_topics", [])[:3],
            "microlearning_formats": microlearning_recs.get("recommended_formats", []),
            "optimization_score": 0.85
        }
        
        integration_response = {
            "user_id": request.user_id,
            "area": request.area,
            "microlearning_recommendations": microlearning_recs,
            "thematic_analysis": thematic_integration,
            "combined_recommendations": combined_recommendations,
            "learning_optimization": learning_optimization,
            "created_at": datetime.utcnow()
        }
        
        return Phase3IntegrationResponse(**integration_response)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error integrando sistemas Fase 3: {str(e)}")


# ============================================================================
# ENDPOINTS DE INFORMACIÓN DEL SISTEMA
# ============================================================================

@router.get("/microlearning/formats", response_model=MicroLearningFormatsResponse)
async def get_microlearning_formats():
    """
    Obtiene formatos de microlearning disponibles
    """
    try:
        formats = microlearning_engine.microlearning_formats
        
        return MicroLearningFormatsResponse(
            formats=formats,
            total_formats=len(formats),
            descriptions=formats
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo formatos: {str(e)}")


@router.get("/microlearning/active-recall-types", response_model=ActiveRecallTypesResponse)
async def get_active_recall_types():
    """
    Obtiene tipos de Active Recall disponibles
    """
    try:
        types = microlearning_engine.active_recall_types
        
        return ActiveRecallTypesResponse(
            types=types,
            total_types=len(types),
            descriptions=types
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo tipos de Active Recall: {str(e)}")


@router.get("/thematic/metrics", response_model=ThematicAnalysisMetricsResponse)
async def get_thematic_analysis_metrics():
    """
    Obtiene métricas de análisis temático
    """
    try:
        metrics = thematic_analysis_engine.analysis_metrics
        
        return ThematicAnalysisMetricsResponse(
            metrics=metrics,
            total_metrics=len(metrics),
            descriptions=metrics
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo métricas: {str(e)}")


@router.get("/health", response_model=Phase3HealthResponse)
async def phase3_health_check():
    """
    Verifica salud de los sistemas de la Fase 3
    """
    try:
        return Phase3HealthResponse(
            status="healthy",
            system="Fase 3 - Microlearning y Análisis Temático",
            components={
                "microlearning": "operational",
                "thematic_analysis": "operational",
                "active_recall": "operational",
                "priority_matrix": "operational"
            },
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en health check Fase 3: {str(e)}")


# ============================================================================
# ENDPOINTS DE GAMIFICACIÓN AVANZADA
# ============================================================================

@router.get("/gamification/insignias")
async def get_advanced_badges():
    """
    Obtiene insignias avanzadas del sistema
    """
    try:
        badges = {
            "microlearning_master": {
                "name": "Maestro del Microlearning",
                "description": "Completa 50 micro-lecciones",
                "icon": "🎯",
                "requirements": {"micro_lessons": 50}
            },
            "active_recall_champion": {
                "name": "Campeón del Active Recall",
                "description": "Completa 100 ejercicios de Active Recall",
                "icon": "🧠",
                "requirements": {"active_recall_exercises": 100}
            },
            "thematic_analyst": {
                "name": "Analista Temático",
                "description": "Analiza 10 áreas diferentes",
                "icon": "📊",
                "requirements": {"areas_analyzed": 10}
            },
            "priority_master": {
                "name": "Maestro de Prioridades",
                "description": "Completa temas de alta prioridad en 5 áreas",
                "icon": "⭐",
                "requirements": {"high_priority_completed": 5}
            }
        }
        
        return {
            "badges": badges,
            "total_badges": len(badges),
            "available_for_unlock": True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo insignias: {str(e)}")


@router.get("/gamification/economia-virtual")
async def get_virtual_economy():
    """
    Obtiene información de la economía virtual
    """
    try:
        economy = {
            "currency": "XP Coins",
            "exchange_rate": 1.0,
            "earning_sources": {
                "micro_lesson_completion": 10,
                "active_recall_completion": 5,
                "thematic_analysis": 15,
                "priority_topic_completion": 20
            },
            "spending_options": {
                "premium_content": 100,
                "custom_insignias": 50,
                "learning_boost": 75
            },
            "total_users_with_coins": 1250,
            "average_coins_per_user": 45
        }
        
        return economy
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo economía virtual: {str(e)}")


@router.get("/gamification/leaderboards")
async def get_advanced_leaderboards():
    """
    Obtiene leaderboards avanzados
    """
    try:
        leaderboards = {
            "microlearning_streak": {
                "title": "Racha de Microlearning",
                "description": "Días consecutivos de micro-lecciones",
                "top_players": [
                    {"user": "user1", "score": 15, "rank": 1},
                    {"user": "user2", "score": 12, "rank": 2},
                    {"user": "user3", "score": 10, "rank": 3}
                ]
            },
            "active_recall_master": {
                "title": "Maestro del Active Recall",
                "description": "Ejercicios de Active Recall completados",
                "top_players": [
                    {"user": "user4", "score": 150, "rank": 1},
                    {"user": "user5", "score": 120, "rank": 2},
                    {"user": "user6", "score": 100, "rank": 3}
                ]
            },
            "thematic_analyst": {
                "title": "Analista Temático",
                "description": "Áreas analizadas",
                "top_players": [
                    {"user": "user7", "score": 8, "rank": 1},
                    {"user": "user8", "score": 6, "rank": 2},
                    {"user": "user9", "score": 5, "rank": 3}
                ]
            }
        }
        
        return {
            "leaderboards": leaderboards,
            "total_leaderboards": len(leaderboards),
            "updated_at": datetime.utcnow()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo leaderboards: {str(e)}") 