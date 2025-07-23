"""
Esquemas de datos para el sistema ITS (Intelligent Tutoring System)
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


# Esquemas para Diagnóstico Inicial
class DiagnosticQuestionRequest(BaseModel):
    user_id: str = Field(..., description="ID del usuario")
    area: str = Field(..., description="Área académica para diagnóstico")


class DiagnosticQuestionResponse(BaseModel):
    assessment_id: str = Field(..., description="ID de la evaluación")
    user_id: str = Field(..., description="ID del usuario")
    area: str = Field(..., description="Área académica")
    total_questions: int = Field(..., description="Total de preguntas")
    estimated_duration: int = Field(..., description="Duración estimada en minutos")
    questions: List[Dict[str, Any]] = Field(..., description="Lista de preguntas")
    status: str = Field(..., description="Estado de la evaluación")
    created_at: datetime = Field(..., description="Fecha de creación")


class DiagnosticAnswerRequest(BaseModel):
    assessment_id: str = Field(..., description="ID de la evaluación")
    user_id: str = Field(..., description="ID del usuario")
    answers: List[Dict[str, Any]] = Field(..., description="Respuestas del usuario")
    time_spent: int = Field(..., description="Tiempo total empleado en segundos")


class KnowledgeMapResponse(BaseModel):
    user_id: str = Field(..., description="ID del usuario")
    area: str = Field(..., description="Área académica")
    overall_score: float = Field(..., description="Puntuación general (0-100)")
    strengths: List[str] = Field(..., description="Temas fuertes")
    weaknesses: List[str] = Field(..., description="Temas débiles")
    recommended_topics: List[str] = Field(..., description="Temas recomendados")
    knowledge_level: str = Field(..., description="Nivel de conocimiento")
    estimated_study_time: int = Field(..., description="Tiempo estimado de estudio en horas")
    created_at: datetime = Field(..., description="Fecha de creación")


class DiagnosticRecommendationResponse(BaseModel):
    user_id: str = Field(..., description="ID del usuario")
    area: str = Field(..., description="Área académica")
    study_plan: List[Dict[str, Any]] = Field(..., description="Plan de estudio")
    priority_topics: List[str] = Field(..., description="Temas prioritarios")
    learning_path: str = Field(..., description="Tipo de ruta de aprendizaje")
    estimated_completion: int = Field(..., description="Tiempo estimado de completación en semanas")
    created_at: datetime = Field(..., description="Fecha de creación")


# Esquemas para Motor Adaptativo
class StudentModelUpdateRequest(BaseModel):
    user_id: str = Field(..., description="ID del usuario")
    topic: str = Field(..., description="Tema específico")
    area: str = Field(..., description="Área académica")
    is_correct: bool = Field(..., description="Si la respuesta fue correcta")
    time_spent: int = Field(..., description="Tiempo empleado en segundos")
    difficulty: int = Field(..., description="Nivel de dificultad (1-3)")


class StudentModelResponse(BaseModel):
    user_id: str = Field(..., description="ID del usuario")
    area: str = Field(..., description="Área académica")
    topic: str = Field(..., description="Tema específico")
    mastery_level: str = Field(..., description="Nivel de dominio")
    mastery_score: float = Field(..., description="Puntuación de dominio (0-1)")
    zpd_zone: str = Field(..., description="Zona de desarrollo próximo")
    performance_metrics: Dict[str, Any] = Field(..., description="Métricas de rendimiento")
    recommended_difficulty: int = Field(..., description="Dificultad recomendada")
    last_updated: datetime = Field(..., description="Última actualización")


class DailyPlanRequest(BaseModel):
    user_id: str = Field(..., description="ID del usuario")
    date: Optional[str] = Field(None, description="Fecha específica (opcional)")


class DailyPlanResponse(BaseModel):
    user_id: str = Field(..., description="ID del usuario")
    date: datetime = Field(..., description="Fecha del plan")
    total_time: int = Field(..., description="Tiempo total en minutos")
    activities: List[Dict[str, Any]] = Field(..., description="Actividades del día")
    goals: List[str] = Field(..., description="Objetivos del día")
    estimated_progress: float = Field(..., description="Progreso estimado")


class ZPDResponse(BaseModel):
    user_id: str = Field(..., description="ID del usuario")
    zpd_topics: List[Dict[str, Any]] = Field(..., description="Temas en zona de desarrollo próximo")
    total_topics: int = Field(..., description="Total de temas en ZPD")
    priority_order: List[str] = Field(..., description="Orden de prioridad")


# Esquemas para Rutas de Aprendizaje
class LearningPathRequest(BaseModel):
    user_id: str = Field(..., description="ID del usuario")
    area: str = Field(..., description="Área académica")


class LearningPathResponse(BaseModel):
    user_id: str = Field(..., description="ID del usuario")
    area: str = Field(..., description="Área académica")
    path_type: str = Field(..., description="Tipo de ruta")
    created_at: datetime = Field(..., description="Fecha de creación")
    estimated_duration: int = Field(..., description="Duración estimada en semanas")
    total_topics: int = Field(..., description="Total de temas")
    milestones: List[Dict[str, Any]] = Field(..., description="Milestones de la ruta")
    checkpoints: List[Dict[str, Any]] = Field(..., description="Checkpoints de evaluación")
    adaptation_rules: List[Dict[str, Any]] = Field(..., description="Reglas de adaptación")


class PathAdaptationRequest(BaseModel):
    user_id: str = Field(..., description="ID del usuario")
    path_id: str = Field(..., description="ID de la ruta")
    performance_data: Dict[str, Any] = Field(..., description="Datos de rendimiento reciente")


class PathAdaptationResponse(BaseModel):
    user_id: str = Field(..., description="ID del usuario")
    path_id: str = Field(..., description="ID de la ruta")
    adaptation_type: str = Field(..., description="Tipo de adaptación")
    triggered_by: Dict[str, Any] = Field(..., description="Factores que dispararon la adaptación")
    actions: List[str] = Field(..., description="Acciones recomendadas")
    estimated_impact: str = Field(..., description="Impacto estimado")
    focus_areas: Optional[List[str]] = Field(None, description="Áreas de enfoque")
    estimated_recovery_time: Optional[int] = Field(None, description="Tiempo estimado de recuperación")
    created_at: datetime = Field(..., description="Fecha de creación")


class PathProgressRequest(BaseModel):
    user_id: str = Field(..., description="ID del usuario")
    path_id: str = Field(..., description="ID de la ruta")


class PathProgressResponse(BaseModel):
    user_id: str = Field(..., description="ID del usuario")
    path_id: str = Field(..., description="ID de la ruta")
    current_milestone: int = Field(..., description="Milestone actual")
    completed_milestones: int = Field(..., description="Milestones completados")
    total_milestones: int = Field(..., description="Total de milestones")
    completion_percentage: float = Field(..., description="Porcentaje de completación")
    estimated_completion_date: datetime = Field(..., description="Fecha estimada de completación")
    streak_days: int = Field(..., description="Días consecutivos de estudio")
    last_activity: datetime = Field(..., description="Última actividad")
    performance_trend: str = Field(..., description="Tendencia de rendimiento")


# Esquemas para Integración ITS-DECO
class ITSDecoIntegrationRequest(BaseModel):
    user_id: str = Field(..., description="ID del usuario")
    area: str = Field(..., description="Área académica")
    topic: str = Field(..., description="Tema específico")
    deco_question_type: str = Field(..., description="Tipo de pregunta DECO")
    difficulty: int = Field(..., description="Nivel de dificultad")


class ITSDecoIntegrationResponse(BaseModel):
    user_id: str = Field(..., description="ID del usuario")
    area: str = Field(..., description="Área académica")
    topic: str = Field(..., description="Tema específico")
    deco_question: Dict[str, Any] = Field(..., description="Pregunta DECO generada")
    student_model_update: Dict[str, Any] = Field(..., description="Actualización del modelo del estudiante")
    recommended_next_topic: str = Field(..., description="Siguiente tema recomendado")
    learning_path_adjustment: Optional[Dict[str, Any]] = Field(None, description="Ajuste de ruta de aprendizaje")
    created_at: datetime = Field(..., description="Fecha de creación") 