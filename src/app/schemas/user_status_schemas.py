from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.models.adaptive import UserChapterStatus # Asegurarse que esta importación sea válida

# Esquema para la información de progreso de cada capítulo estudiado
class ChapterProgressInfo(BaseModel):
    chapter_id: int
    chapter_title: str
    status: UserChapterStatus # Usar el Enum directamente
    percentage: int

    class Config:
        from_attributes = True

# Esquema para la información de los capítulos sugeridos por SRS
class SRSSuggestionInfo(BaseModel):
    chapter_id: int
    chapter_title: str
    next_due: datetime

    class Config:
        from_attributes = True

# Esquema para datos de progreso general del usuario
class UserProgressData(BaseModel):
    total_lessons_completed: int = 0
    total_chapters_mastered: int = 0
    # overall_accuracy: Optional[float] = Field(None, ge=0, le=100) # Ya está en UserStatusResponse

    class Config:
        from_attributes = True

# Esquema para la respuesta del endpoint /user/status
class UserStatusResponse(BaseModel):
    # Campos existentes (basados en la implementación actual y discusión previa)
    user_id_hash: str
    course: str
    total_xp: int
    current_streak: int
    longest_streak: int
    leaderboard_rank_global_weekly: Optional[int] = None # Mantener este de la implementación anterior
    
    # Nuevos campos
    user_progress: Optional[UserProgressData] # Progreso general del usuario
    overall_accuracy: Optional[float] = Field(None, description="Precisión general del usuario en todas las unidades completadas, de 0 a 100", ge=0, le=100)
    studied_chapters: List[ChapterProgressInfo] = Field(default_factory=list)
    srs_suggestions: List[SRSSuggestionInfo] = Field(default_factory=list)

    class Config:
        from_attributes = True

# --- Esquemas para la visualización del progreso del alumno por el profesor ---

class AlumnoProgresoCapituloInfo(BaseModel):
    """Información de progreso de un alumno en un capítulo específico."""
    capitulo_id: int
    capitulo_titulo: str
    estado: UserChapterStatus # Reutilizamos el enum existente
    porcentaje_completado: int = Field(..., ge=0, le=100)
    estrellas: int = Field(..., ge=0, le=3)
    # Podríamos añadir más detalles si es necesario, como fecha de último estudio, etc.

    class Config:
        from_attributes = True

class AlumnoProgresoCursoInfo(BaseModel):
    """Información de progreso de un alumno en un curso específico, detallado por capítulos."""
    curso_id: int
    curso_nombre: str
    progreso_general_curso: int = Field(..., ge=0, le=100) # Porcentaje completado del curso
    capitulos_progreso: List[AlumnoProgresoCapituloInfo] = Field(default_factory=list)

    class Config:
        from_attributes = True

class AlumnoClaseProgresoResponse(BaseModel):
    """Respuesta para el endpoint de progreso de un alumno en una clase específica."""
    user_id_hash: str
    clase_id: int
    #clase_nombre: str # Podríamos añadir el nombre de la clase para contexto
    progreso_por_curso: List[AlumnoProgresoCursoInfo] = Field(default_factory=list) 