"""
Schemas Pydantic para el sistema DECO (DEstrezas COgnitivas)
Implementa validación de datos para preguntas tipo UNMSM 2025
"""

from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class DECOQuestionRequest(BaseModel):
    """Schema para solicitar una pregunta DECO"""
    model_config = ConfigDict(from_attributes=True)
    
    user_id: str = Field(..., description="ID único del usuario")
    area: str = Field(..., description="Área académica (ej: 'Ciencias', 'Letras')")
    topic: Optional[str] = Field(None, description="Tema específico de la pregunta (opcional)")
    difficulty: int = Field(default=2, ge=1, le=3, description="Nivel de dificultad (1-3)")
    cognitive_skill: Optional[str] = Field(None, description="Habilidad cognitiva específica")
    chapter_id: Optional[int] = Field(None, description="ID del capítulo para usar como contexto (opcional, pero recomendado)")


class DECOTheoryResponse(BaseModel):
    """
    Schema para la respuesta de teoría de DECO.
    Esto no es una pregunta completa, sino el material para que el LLM la genere.
    """
    model_config = ConfigDict(from_attributes=True)
    
    course: str = Field(..., description="Nombre del curso")
    topic: str = Field(..., description="Tema del capítulo")
    source_chapter: str = Field(..., description="Título del capítulo de origen")
    theory_content: str = Field(..., description="Contenido teórico extraído")
    instruction: str = Field(default="generate_question_from_theory", description="Instrucción para el LLM")
    metadata: Dict = Field(..., description="Metadatos adicionales como chapter_id")


class DECOQuestionResponse(BaseModel):
    """Schema para respuesta de pregunta DECO"""
    model_config = ConfigDict(from_attributes=True)
    
    session_id: str = Field(..., description="ID único de la sesión")
    user_id: str = Field(..., description="ID del usuario")
    area: str = Field(..., description="Área académica")
    topic: str = Field(..., description="Tema específico")
    difficulty: int = Field(..., description="Nivel de dificultad")
    cognitive_skill: str = Field(..., description="Habilidad cognitiva evaluada")
    context: str = Field(..., description="Cotexto de la pregunta")
    question: str = Field(..., description="Pregunta DECO")
    alternatives: Dict[str, str] = Field(..., description="Alternativas A, B, C, D")
    correct_answer: str = Field(..., description="Respuesta correcta")
    explanation: str = Field(..., description="Explicación de la respuesta")
    created_at: datetime = Field(..., description="Fecha de creación")


class DECOAnswerRequest(BaseModel):
    """Schema para enviar respuesta a pregunta DECO"""
    model_config = ConfigDict(from_attributes=True)
    
    session_id: str = Field(..., description="ID de la sesión DECO, usualmente el título del capítulo o un ID numérico.")
    user_id: str = Field(..., description="ID del usuario")
    answer: str = Field(..., description="Respuesta del usuario (A, B, C, D)")
    is_correct: bool = Field(..., description="El Custom GPT debe indicar si la respuesta fue correcta.")
    area: str = Field(..., description="Área académica (enviada por el GPT)")
    topic: str = Field(..., description="Tema específico (enviado por el GPT)")
    time_spent: Optional[int] = Field(None, description="Tiempo en segundos")


class DECOAnswerResponse(BaseModel):
    """Schema para respuesta de evaluación DECO"""
    model_config = ConfigDict(from_attributes=True)
    
    session_id: str = Field(..., description="ID de la sesión")
    user_id: str = Field(..., description="ID del usuario")
    is_correct: bool = Field(..., description="Si la respuesta es correcta")
    user_answer: str = Field(..., description="Respuesta del usuario")
    correct_answer: str = Field(..., description="Respuesta correcta")
    feedback: str = Field(..., description="Retroalimentación adaptativa")
    micro_lesson: str = Field(..., description="Micro-lección sobre el tema")
    cognitive_skill: str = Field(..., description="Habilidad cognitiva evaluada")
    topic: str = Field(..., description="Tema evaluado")
    area: str = Field(..., description="Área académica")
    difficulty: int = Field(..., description="Nivel de dificultad")
    points_earned: int = Field(..., description="Puntos ganados")
    created_at: datetime = Field(..., description="Fecha de evaluación")


class DECOSessionRequest(BaseModel):
    """Schema para crear sesión DECO completa"""
    model_config = ConfigDict(from_attributes=True)
    
    user_id: str = Field(..., description="ID del usuario")
    area: str = Field(..., description="Área académica")
    topic: str = Field(..., description="Tema específico")
    difficulty: int = Field(default=2, ge=1, le=3, description="Nivel de dificultad")
    session_type: str = Field(default="practice", description="Tipo de sesión (practice, assessment)")


class DECOSessionResponse(BaseModel):
    """Schema para respuesta de sesión DECO"""
    model_config = ConfigDict(from_attributes=True)
    
    session_id: str = Field(..., description="ID único de la sesión")
    user_id: str = Field(..., description="ID del usuario")
    area: str = Field(..., description="Área académica")
    topic: str = Field(..., description="Tema específico")
    difficulty: int = Field(..., description="Nivel de dificultad")
    cognitive_skill: str = Field(..., description="Habilidad cognitiva")
    context: str = Field(..., description="Cotexto de la pregunta")
    question: str = Field(..., description="Pregunta DECO")
    alternatives: Dict[str, str] = Field(..., description="Alternativas")
    correct_answer: str = Field(..., description="Respuesta correcta")
    explanation: str = Field(..., description="Explicación")
    session_type: str = Field(..., description="Tipo de sesión")
    created_at: datetime = Field(..., description="Fecha de creación")


class DECOProgressRequest(BaseModel):
    """Schema para solicitar progreso DECO del usuario"""
    model_config = ConfigDict(from_attributes=True)
    
    user_id: str = Field(..., description="ID del usuario")
    area: Optional[str] = Field(None, description="Área específica (opcional)")
    topic: Optional[str] = Field(None, description="Tema específico (opcional)")
    days: Optional[int] = Field(default=30, description="Días hacia atrás")


class DECOProgressResponse(BaseModel):
    """Schema para respuesta de progreso DECO"""
    model_config = ConfigDict(from_attributes=True)
    
    user_id: str = Field(..., description="ID del usuario")
    total_sessions: int = Field(..., description="Total de sesiones DECO")
    correct_answers: int = Field(..., description="Respuestas correctas")
    incorrect_answers: int = Field(..., description="Respuestas incorrectas")
    accuracy_rate: float = Field(..., description="Tasa de precisión")
    topics_covered: List[str] = Field(..., description="Temas cubiertos")
    cognitive_skills_practiced: List[str] = Field(..., description="Habilidades cognitivas practicadas")
    average_difficulty: float = Field(..., description="Dificultad promedio")
    total_points: int = Field(..., description="Puntos totales ganados")
    progress_by_area: Dict[str, Dict] = Field(..., description="Progreso por área académica")
    progress_by_topic: Dict[str, Dict] = Field(..., description="Progreso por tema")
    created_at: datetime = Field(..., description="Fecha del reporte")


class DECORecommendationRequest(BaseModel):
    """Schema para solicitar recomendaciones DECO"""
    model_config = ConfigDict(from_attributes=True)
    
    user_id: str = Field(..., description="ID del usuario")
    area: Optional[str] = Field(None, description="Área específica")
    difficulty_preference: Optional[int] = Field(None, ge=1, le=3, description="Preferencia de dificultad")


class DECORecommendationResponse(BaseModel):
    """Schema para respuesta de recomendaciones DECO"""
    model_config = ConfigDict(from_attributes=True)
    
    user_id: str = Field(..., description="ID del usuario")
    recommended_topics: List[Dict] = Field(..., description="Temas recomendados")
    recommended_cognitive_skills: List[str] = Field(..., description="Habilidades cognitivas a practicar")
    study_plan: Dict = Field(..., description="Plan de estudio personalizado")
    weak_areas: List[str] = Field(..., description="Áreas débiles identificadas")
    strong_areas: List[str] = Field(..., description="Áreas fuertes identificadas")
    next_session_recommendation: Optional[Dict] = Field(None, description="Recomendación para próxima sesión")
    created_at: datetime = Field(..., description="Fecha de la recomendación")


class DECOContextTemplate(BaseModel):
    """Schema para templates de contexto DECO"""
    model_config = ConfigDict(from_attributes=True)
    
    area: str = Field(..., description="Área académica")
    template_text: str = Field(..., description="Texto del template")
    difficulty_level: int = Field(..., description="Nivel de dificultad")
    cognitive_skill: str = Field(..., description="Habilidad cognitiva asociada")
    is_active: bool = Field(default=True, description="Si el template está activo")


class DECOCognitiveSkill(BaseModel):
    """Schema para habilidades cognitivas DECO"""
    model_config = ConfigDict(from_attributes=True)
    
    skill_name: str = Field(..., description="Nombre de la habilidad")
    description: str = Field(..., description="Descripción de la habilidad")
    difficulty_level: int = Field(..., description="Nivel de dificultad típico")
    applicable_areas: List[str] = Field(..., description="Áreas donde se aplica")
    examples: List[str] = Field(..., description="Ejemplos de aplicación") 