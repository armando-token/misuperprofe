"""
Esquemas de datos para la Fase 3: Microlearning y Análisis Temático
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pydantic import BaseModel, Field


# Esquemas para Microlearning
class MicroLessonRequest(BaseModel):
    topic: str = Field(..., description="Tema específico")
    area: str = Field(..., description="Área académica")
    difficulty: int = Field(2, description="Nivel de dificultad (1-3)")


class MicroLessonResponse(BaseModel):
    lesson_id: str = Field(..., description="ID de la micro-lección")
    topic: str = Field(..., description="Tema específico")
    area: str = Field(..., description="Área académica")
    format: str = Field(..., description="Formato de la lección")
    difficulty: int = Field(..., description="Nivel de dificultad")
    duration: int = Field(..., description="Duración en segundos")
    content: Dict[str, Any] = Field(..., description="Contenido de la lección")
    active_recall: Dict[str, Any] = Field(..., description="Ejercicio de Active Recall")
    estimated_completion_time: int = Field(..., description="Tiempo estimado de completación")
    created_at: datetime = Field(..., description="Fecha de creación")


class MicroLearningSeriesRequest(BaseModel):
    topics: List[str] = Field(..., description="Lista de temas")
    area: str = Field(..., description="Área académica")


class MicroLearningSeriesResponse(BaseModel):
    series_id: str = Field(..., description="ID de la serie")
    area: str = Field(..., description="Área académica")
    total_topics: int = Field(..., description="Total de temas")
    estimated_duration: int = Field(..., description="Duración estimada en minutos")
    lessons: List[Dict[str, Any]] = Field(..., description="Lista de lecciones")
    created_at: datetime = Field(..., description="Fecha de creación")


class MicroLearningRecommendationsRequest(BaseModel):
    user_id: str = Field(..., description="ID del usuario")
    area: str = Field(..., description="Área académica")


class MicroLearningRecommendationsResponse(BaseModel):
    user_id: str = Field(..., description="ID del usuario")
    area: str = Field(..., description="Área académica")
    daily_micro_lessons: int = Field(..., description="Número de micro-lecciones diarias")
    recommended_formats: List[str] = Field(..., description="Formatos recomendados")
    topics_for_today: List[str] = Field(..., description="Temas para hoy")
    estimated_time: int = Field(..., description="Tiempo estimado en minutos")
    difficulty_adjustment: str = Field(..., description="Ajuste de dificultad")
    created_at: datetime = Field(..., description="Fecha de creación")


class MicroLearningProgressRequest(BaseModel):
    user_id: str = Field(..., description="ID del usuario")
    lesson_id: str = Field(..., description="ID de la lección")
    completion_data: Dict[str, Any] = Field(..., description="Datos de completación")


class MicroLearningProgressResponse(BaseModel):
    user_id: str = Field(..., description="ID del usuario")
    lesson_id: str = Field(..., description="ID de la lección")
    completed_at: datetime = Field(..., description="Fecha de completación")
    time_spent: int = Field(..., description="Tiempo empleado en segundos")
    score: float = Field(..., description="Puntuación obtenida")
    format_type: str = Field(..., description="Tipo de formato")
    active_recall_completed: bool = Field(..., description="Si completó Active Recall")
    xp_earned: int = Field(..., description="XP ganado")
    streak_updated: bool = Field(..., description="Si se actualizó la racha")


# Esquemas para Análisis Temático
class TopicFrequencyRequest(BaseModel):
    area: str = Field(..., description="Área académica")
    time_period: str = Field("30d", description="Período de análisis")


class TopicFrequencyResponse(BaseModel):
    area: str = Field(..., description="Área académica")
    time_period: str = Field(..., description="Período de análisis")
    total_topics: int = Field(..., description="Total de temas")
    total_appearances: int = Field(..., description="Total de apariciones")
    avg_success_rate: float = Field(..., description="Tasa de éxito promedio")
    frequency_ranking: List[Tuple[str, Dict[str, Any]]] = Field(..., description="Ranking de frecuencia")
    topic_analysis: Dict[str, Dict[str, Any]] = Field(..., description="Análisis por tema")
    created_at: datetime = Field(..., description="Fecha de creación")


class PriorityMatrixRequest(BaseModel):
    area: str = Field(..., description="Área académica")


class PriorityMatrixResponse(BaseModel):
    area: str = Field(..., description="Área académica")
    total_topics: int = Field(..., description="Total de temas")
    priority_matrix: Dict[str, Dict[str, Any]] = Field(..., description="Matriz de priorización")
    top_priority_topics: List[str] = Field(..., description="Temas de alta prioridad")
    low_priority_topics: List[str] = Field(..., description="Temas de baja prioridad")
    created_at: datetime = Field(..., description="Fecha de creación")


class ThematicInsightsRequest(BaseModel):
    area: str = Field(..., description="Área académica")


class ThematicInsightsResponse(BaseModel):
    area: str = Field(..., description="Área académica")
    total_insights: int = Field(..., description="Total de insights")
    key_findings: List[Dict[str, Any]] = Field(..., description="Hallazgos clave")
    recommendations: List[Dict[str, Any]] = Field(..., description="Recomendaciones")
    trends: List[Dict[str, Any]] = Field(..., description="Tendencias identificadas")
    created_at: datetime = Field(..., description="Fecha de creación")


class ThematicIntegrationRequest(BaseModel):
    area: str = Field(..., description="Área académica")
    user_id: str = Field(..., description="ID del usuario")


class ThematicIntegrationResponse(BaseModel):
    user_id: str = Field(..., description="ID del usuario")
    area: str = Field(..., description="Área académica")
    thematic_insights: Dict[str, Any] = Field(..., description="Insights temáticos")
    priority_matrix: Dict[str, Any] = Field(..., description="Matriz de priorización")
    personalized_recommendations: List[Dict[str, Any]] = Field(..., description="Recomendaciones personalizadas")
    learning_path_adjustments: List[Dict[str, Any]] = Field(..., description="Ajustes de ruta de aprendizaje")
    created_at: datetime = Field(..., description="Fecha de creación")


# Esquemas para Integración Fase 3
class Phase3IntegrationRequest(BaseModel):
    user_id: str = Field(..., description="ID del usuario")
    area: str = Field(..., description="Área académica")
    integration_type: str = Field(..., description="Tipo de integración")


class Phase3IntegrationResponse(BaseModel):
    user_id: str = Field(..., description="ID del usuario")
    area: str = Field(..., description="Área académica")
    microlearning_recommendations: Dict[str, Any] = Field(..., description="Recomendaciones de microlearning")
    thematic_analysis: Dict[str, Any] = Field(..., description="Análisis temático")
    combined_recommendations: List[Dict[str, Any]] = Field(..., description="Recomendaciones combinadas")
    learning_optimization: Dict[str, Any] = Field(..., description="Optimización de aprendizaje")
    created_at: datetime = Field(..., description="Fecha de creación")


# Esquemas para Información del Sistema
class MicroLearningFormatsResponse(BaseModel):
    formats: Dict[str, str] = Field(..., description="Formatos disponibles")
    total_formats: int = Field(..., description="Total de formatos")
    descriptions: Dict[str, str] = Field(..., description="Descripciones de formatos")


class ActiveRecallTypesResponse(BaseModel):
    types: Dict[str, str] = Field(..., description="Tipos de Active Recall")
    total_types: int = Field(..., description="Total de tipos")
    descriptions: Dict[str, str] = Field(..., description="Descripciones de tipos")


class ThematicAnalysisMetricsResponse(BaseModel):
    metrics: Dict[str, str] = Field(..., description="Métricas de análisis")
    total_metrics: int = Field(..., description="Total de métricas")
    descriptions: Dict[str, str] = Field(..., description="Descripciones de métricas")


class Phase3HealthResponse(BaseModel):
    status: str = Field(..., description="Estado del sistema")
    system: str = Field(..., description="Sistema")
    components: Dict[str, str] = Field(..., description="Componentes")
    timestamp: datetime = Field(..., description="Timestamp") 