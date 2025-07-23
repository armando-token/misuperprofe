"""
Endpoints REST para el sistema ITS (Intelligent Tutoring System)
Implementa diagnóstico inicial, motor adaptativo y rutas de aprendizaje
"""

from typing import Dict, List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_session as get_db
from app.services.its_diagnostic import its_diagnostic
from app.services.adaptive_learning import adaptive_learning_engine
from app.services.learning_paths import learning_path_generator
from app.schemas.its_schemas import (
    DiagnosticQuestionRequest, DiagnosticQuestionResponse,
    DiagnosticAnswerRequest, KnowledgeMapResponse,
    DiagnosticRecommendationResponse, StudentModelUpdateRequest,
    StudentModelResponse, DailyPlanRequest, DailyPlanResponse,
    ZPDResponse, LearningPathRequest, LearningPathResponse,
    PathAdaptationRequest, PathAdaptationResponse,
    PathProgressRequest, PathProgressResponse,
    ITSDecoIntegrationRequest, ITSDecoIntegrationResponse
)

router = APIRouter(prefix="/its", tags=["ITS - Intelligent Tutoring System"])


# ============================================================================
# ENDPOINTS DE DIAGNÓSTICO INICIAL
# ============================================================================

@router.post("/diagnostic/question", response_model=DiagnosticQuestionResponse)
async def create_diagnostic_assessment(
    request: DiagnosticQuestionRequest,
    db: Session = Depends(get_db)
):
    """
    Crea evaluación de diagnóstico inicial para un área específica
    """
    try:
        assessment = its_diagnostic.create_initial_assessment(
            user_id=request.user_id,
            area=request.area
        )
        
        return DiagnosticQuestionResponse(**assessment)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creando evaluación de diagnóstico: {str(e)}")


@router.post("/diagnostic/answer", response_model=KnowledgeMapResponse)
async def submit_diagnostic_answers(
    request: DiagnosticAnswerRequest,
    db: Session = Depends(get_db)
):
    """
    Procesa respuestas del diagnóstico y genera mapa de conocimiento
    """
    try:
        # Procesar respuestas y generar resultados
        results = {
            "user_id": request.user_id,
            "area": "matematicas",  # TODO: Obtener desde assessment
            "answers": request.answers,
            "time_spent": request.time_spent
        }
        
        # Generar mapa de conocimiento
        knowledge_map = its_diagnostic.generate_knowledge_map(results)
        
        return KnowledgeMapResponse(**knowledge_map)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando respuestas de diagnóstico: {str(e)}")


@router.post("/diagnostic/recommendations", response_model=DiagnosticRecommendationResponse)
async def get_diagnostic_recommendations(
    knowledge_map: KnowledgeMapResponse,
    db: Session = Depends(get_db)
):
    """
    Genera recomendaciones basadas en el mapa de conocimiento
    """
    try:
        recommendations = its_diagnostic.get_diagnostic_recommendations(
            knowledge_map.dict()
        )
        
        return DiagnosticRecommendationResponse(**recommendations)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando recomendaciones: {str(e)}")


# ============================================================================
# ENDPOINTS DEL MOTOR ADAPTATIVO
# ============================================================================

@router.post("/student-model/update", response_model=StudentModelResponse)
async def update_student_model(
    request: StudentModelUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Actualiza modelo del estudiante basado en interacción reciente
    """
    try:
        interaction = {
            "topic": request.topic,
            "area": request.area,
            "is_correct": request.is_correct,
            "time_spent": request.time_spent,
            "difficulty": request.difficulty
        }
        
        updated_model = adaptive_learning_engine.update_student_model(
            user_id=request.user_id,
            interaction=interaction
        )
        
        return StudentModelResponse(**updated_model)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error actualizando modelo del estudiante: {str(e)}")


@router.post("/daily-plan", response_model=DailyPlanResponse)
async def generate_daily_plan(
    request: DailyPlanRequest,
    db: Session = Depends(get_db)
):
    """
    Genera plan de estudio diario personalizado
    """
    try:
        daily_plan = adaptive_learning_engine.generate_daily_plan(
            user_id=request.user_id
        )
        
        return DailyPlanResponse(**daily_plan)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando plan diario: {str(e)}")


@router.get("/zpd", response_model=ZPDResponse)
async def get_zone_of_proximal_development(
    user_id: str = Query(..., description="ID del usuario"),
    db: Session = Depends(get_db)
):
    """
    Identifica temas en zona de desarrollo próximo
    """
    try:
        zpd_topics = adaptive_learning_engine.calculate_zone_of_proximal_development(
            user_id=user_id
        )
        
        response = {
            "user_id": user_id,
            "zpd_topics": zpd_topics,
            "total_topics": len(zpd_topics),
            "priority_order": [topic["topic"] for topic in zpd_topics]
        }
        
        return ZPDResponse(**response)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculando ZPD: {str(e)}")


# ============================================================================
# ENDPOINTS DE RUTAS DE APRENDIZAJE
# ============================================================================

@router.post("/learning-path", response_model=LearningPathResponse)
async def create_learning_path(
    request: LearningPathRequest,
    db: Session = Depends(get_db)
):
    """
    Crea ruta de aprendizaje personalizada
    """
    try:
        learning_path = learning_path_generator.create_personalized_path(
            user_id=request.user_id,
            area=request.area
        )
        
        return LearningPathResponse(**learning_path)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creando ruta de aprendizaje: {str(e)}")


@router.post("/learning-path/adapt", response_model=PathAdaptationResponse)
async def adapt_learning_path(
    request: PathAdaptationRequest,
    db: Session = Depends(get_db)
):
    """
    Adapta ruta de aprendizaje basada en rendimiento reciente
    """
    try:
        adaptation = learning_path_generator.adapt_path_dynamically(
            user_id=request.user_id,
            performance_data=request.performance_data
        )
        
        adaptation["path_id"] = request.path_id
        
        return PathAdaptationResponse(**adaptation)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adaptando ruta de aprendizaje: {str(e)}")


@router.get("/learning-path/progress", response_model=PathProgressResponse)
async def get_learning_path_progress(
    user_id: str = Query(..., description="ID del usuario"),
    path_id: str = Query(..., description="ID de la ruta"),
    db: Session = Depends(get_db)
):
    """
    Obtiene progreso actual de la ruta de aprendizaje
    """
    try:
        progress = learning_path_generator.get_path_progress(
            user_id=user_id,
            path_id=path_id
        )
        
        return PathProgressResponse(**progress)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo progreso de ruta: {str(e)}")


# ============================================================================
# ENDPOINTS DE INTEGRACIÓN ITS-DECO
# ============================================================================

@router.post("/deco-integration", response_model=ITSDecoIntegrationResponse)
async def integrate_its_with_deco(
    request: ITSDecoIntegrationRequest,
    db: Session = Depends(get_db)
):
    """
    Integra sistema ITS con preguntas DECO
    """
    try:
        # TODO: Implementar integración completa ITS-DECO
        # Por ahora, generar respuesta mock
        
        integration_response = {
            "user_id": request.user_id,
            "area": request.area,
            "topic": request.topic,
            "deco_question": {
                "question": f"Pregunta DECO de {request.topic}",
                "alternatives": {"A": "Opción A", "B": "Opción B", "C": "Opción C", "D": "Opción D"},
                "correct_answer": "A",
                "difficulty": request.difficulty
            },
            "student_model_update": {
                "mastery_level": "developing",
                "zpd_zone": "learning_zone",
                "recommended_difficulty": request.difficulty
            },
            "recommended_next_topic": "siguiente_tema",
            "learning_path_adjustment": {
                "adaptation_type": "maintain",
                "actions": ["Continuar con progreso actual"]
            },
            "created_at": datetime.utcnow()
        }
        
        return ITSDecoIntegrationResponse(**integration_response)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error integrando ITS con DECO: {str(e)}")


# ============================================================================
# ENDPOINTS DE INFORMACIÓN DEL SISTEMA
# ============================================================================

@router.get("/path-types")
async def get_learning_path_types():
    """
    Obtiene tipos de rutas de aprendizaje disponibles
    """
    try:
        path_types = learning_path_generator.path_types
        
        return {
            "path_types": path_types,
            "total_types": len(path_types),
            "descriptions": path_types
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo tipos de rutas: {str(e)}")


@router.get("/areas")
async def get_its_areas():
    """
    Obtiene áreas académicas disponibles para ITS
    """
    try:
        areas = list(its_diagnostic.fundamental_topics.keys())
        
        return {
            "areas": areas,
            "total_areas": len(areas),
            "available_for_its": True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo áreas ITS: {str(e)}")


@router.get("/health")
async def its_health_check():
    """
    Verifica salud del sistema ITS
    """
    try:
        return {
            "status": "healthy",
            "system": "ITS - Intelligent Tutoring System",
            "components": {
                "diagnostic": "operational",
                "adaptive_learning": "operational",
                "learning_paths": "operational"
            },
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en health check ITS: {str(e)}") 