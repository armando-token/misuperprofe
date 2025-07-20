from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

# Esquemas para el inicio de la lección
class StartLessonRequest(BaseModel):
    # user_id_hash: Optional[str] = None # Se obtendrá del token JWT OAuth
    course: Optional[str] = None
    # unit_id es el ID de la unidad/tema DENTRO del curso. Es opcional.
    # Si no se proporciona, el sistema puede elegir uno (ej. el siguiente en el SRS).
    unit_id: Optional[int] = None # Esto podría mapearse a chapter_id
    # chapter_id es una forma más explícita de solicitar un capítulo específico por su ID global.
    chapter_id: Optional[int] = None 
    # lesson_type: Optional[str] = "adaptive" # Podría usarse para diferenciar tipos de lecciones

# ... el resto del archivo ... 