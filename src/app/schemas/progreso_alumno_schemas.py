from pydantic import BaseModel
from typing import List, Optional
from app.models.adaptive import UserChapterStatus # Importar el Enum del modelo

class ProgresoCapituloParaProfesor(BaseModel):
    id_capitulo: int
    titulo_capitulo: str
    estado: UserChapterStatus
    porcentaje_completado: int

    class Config:
        from_attributes = True

class ProgresoCursoParaProfesor(BaseModel):
    id_curso: int
    nombre_curso: str
    progreso_general_curso: int
    capitulos: List[ProgresoCapituloParaProfesor]

    class Config:
        from_attributes = True

class ProgresoAlumnoGlobal(BaseModel):
    user_id_hash: str
    xp_total: int
    racha_actual: int
    # Aquí se podrían añadir más campos globales si es necesario,
    # como racha_mas_larga, temas_dominados_count, etc.

    class Config:
        from_attributes = True 