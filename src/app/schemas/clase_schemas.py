from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.schemas.profesor_schemas import ProfesorPublic # Para anidar info del profesor
from app.schemas.curso import CursoPublico # Importar CursoPublico

class GrupoClaseBase(BaseModel):
    nombre_clase: str = Field(..., min_length=3, max_length=255)
    descripcion: Optional[str] = None

class GrupoClaseCreate(GrupoClaseBase):
    curso_ids: Optional[List[int]] = Field(default_factory=list, description="Lista de IDs de los cursos a asociar con esta clase.")

class GrupoClaseUpdate(GrupoClaseBase):
    nombre_clase: Optional[str] = Field(None, min_length=3, max_length=255)
    # Otros campos que se puedan actualizar

class GrupoClasePublic(GrupoClaseBase):
    id: int
    codigo_clase: Optional[str] = None
    created_at: datetime
    cursos: List[CursoPublico] = [] # Añadir lista de cursos

    model_config = ConfigDict(from_attributes=True)

class AlumnoEnClaseInfo(BaseModel):
    user_id_hash: str
    fecha_inscripcion: datetime
    # Aquí podríamos añadir más adelante el nombre/email del alumno si se decide crear un modelo Alumno

    model_config = ConfigDict(from_attributes=True)

class GrupoClaseConDetallesPublic(GrupoClasePublic):
    profesores: List[ProfesorPublic] = [] # Lista de profesores asociados
    alumnos: List[AlumnoEnClaseInfo] = []  # Lista de alumnos inscritos
    # Los cursos ya estarán en GrupoClasePublic, así que no es necesario repetirlos aquí si hereda.

# Nuevo esquema para la respuesta de /join, incluye alumnos y hereda cursos de GrupoClasePublic
class GrupoClasePublicConAlumnos(GrupoClasePublic):
    alumnos_association: List[AlumnoEnClaseInfo] = Field(default_factory=list, alias="alumnos")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

# Esquema para que un alumno se una a una clase con un código
class CodigoClaseJoin(BaseModel):
    codigo_clase: str = Field(..., min_length=5, max_length=50)

# Esquema para la petición de un alumno para unirse a una clase
class AlumnoUnirseClaseRequest(BaseModel):
    codigo_clase: str = Field(..., description="Código de la clase a la que unirse.")

# Esquema para que un profesor añada un alumno a una clase (opcionalmente)
class ClaseAlumnoAdd(BaseModel):
    user_id_hash: str 

# Esquema de respuesta simple para depuración
class SimpleSuccessResponse(BaseModel):
    message: str
    detail: Optional[str] = None
    clase_id: Optional[int] = None
    user_id_hash_inscrito: Optional[str] = None 