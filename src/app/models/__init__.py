# Este archivo asegura que todos los modelos SQLAlchemy sean conocidos por Alembic.

# Importar Base primero, aunque los modelos individuales también lo importan.
from .base import Base

# Modelos existentes (asegurarse de que estén todos)
from .curso import Curso
from .capitulo import Capitulo
from .adaptive import (
    LessonSession, 
    UserProgress, 
    Streak, 
    LessonError, 
    ProgressUnit, 
    GrowthLog, 
    SpacedRepetition, 
    AchievementsLog, 
    Attempt,
    UserChapterStatus # Enum también puede ser útil que esté disponible
)
from .resultado import Resultado

# Nuevos modelos para funcionalidades de profesor
from .profesor import Profesor
from .clase import GrupoClase
from .associations import profesor_grupo_clase_association, GrupoClaseAlumnoAssociation, grupo_clase_curso_association

# Nuevos modelos para integración con ChatGPT Team
from .role_enums import MisuperprofeRole
from .external_user_map import ExternalUserMap

__all__ = [
    "Base",
    "Curso",
    "Capitulo",
    "LessonSession",
    "UserProgress",
    "Streak",
    "LessonError",
    "ProgressUnit",
    "GrowthLog",
    "SpacedRepetition",
    "AchievementsLog",
    "Attempt",
    "UserChapterStatus",
    "Resultado",
    "Profesor",
    "GrupoClase",
    "profesor_grupo_clase_association",
    "GrupoClaseAlumnoAssociation",
    "grupo_clase_curso_association",
    "MisuperprofeRole",
    "ExternalUserMap",
]
