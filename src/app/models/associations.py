from sqlalchemy import Table, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base # Asumiendo que Base está en app.models.base
from app.db.custom_types import NaiveDateTime # Para created_at, updated_at

# Tabla de Asociación para la relación muchos-a-muchos entre Profesor y GrupoClase
# Esta tabla no tiene columnas adicionales más allá de las claves foráneas.
profesor_grupo_clase_association = Table(
    'profesor_grupo_clase_association', 
    Base.metadata,
    Column('profesor_id', Integer, ForeignKey('profesor.id', ondelete="CASCADE"), primary_key=True),
    Column('grupo_clase_id', Integer, ForeignKey('grupo_clase.id', ondelete="CASCADE"), primary_key=True)
)

# Tabla de Asociación para la relación muchos-a-muchos entre GrupoClase y Curso
grupo_clase_curso_association = Table(
    'grupo_clase_curso_association',
    Base.metadata,
    Column('grupo_clase_id', Integer, ForeignKey('grupo_clase.id', ondelete="CASCADE"), primary_key=True),
    Column('curso_id', Integer, ForeignKey('curso.id', ondelete="CASCADE"), primary_key=True)
)

# Clase de Asociación para la relación muchos-a-muchos entre GrupoClase y Alumno (user_id_hash)
# Se usa una clase mapeada porque tenemos datos adicionales en la relación (ej. fecha_inscripcion).
class GrupoClaseAlumnoAssociation(Base):
    __tablename__ = 'grupo_clase_alumno_association'

    grupo_clase_id = Column(Integer, ForeignKey('grupo_clase.id', ondelete="CASCADE"), primary_key=True)
    user_id_hash = Column(String(64), primary_key=True, index=True) # Coincide con UserProgress.user_id_hash
    
    fecha_inscripcion = Column(NaiveDateTime, server_default=func.now(), nullable=False)

    # Relación de vuelta a GrupoClase
    # Esto permite, por ejemplo, acceder a la clase desde una instancia de esta asociación.
    grupo_clase = relationship("GrupoClase", back_populates="alumnos_association")

    # No hay una relación directa a un modelo "Alumno" o "UserProgress" desde aquí para evitar complejidad
    # con la clave primaria compuesta de UserProgress (user_id_hash, course).
    # El user_id_hash es el enlace al alumno.
    # Los datos de progreso del alumno (UserProgress) se consultarán usando este user_id_hash y un course_id.

    def __repr__(self):
        return f"<GrupoClaseAlumnoAssociation clase_id={self.grupo_clase_id} user='{self.user_id_hash}'>" 