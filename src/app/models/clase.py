from sqlalchemy import Column, Integer, String, Text, Table, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base # Asumiendo que Base está en app.models.base
from app.db.custom_types import NaiveDateTime # Para created_at, updated_at
from sqlalchemy.sql import func # Para server_default

# Importar las tablas/clases de asociación definidas en associations.py
from .associations import profesor_grupo_clase_association, GrupoClaseAlumnoAssociation, grupo_clase_curso_association

# Importar la tabla de asociación si se define en associations.py
# from .associations import profesor_clase_association, clase_alumno_association

class GrupoClase(Base):
    __tablename__ = "grupo_clase"

    id = Column(Integer, primary_key=True, index=True)
    nombre_clase = Column(String(255), nullable=False, index=True)
    descripcion = Column(Text)
    codigo_clase = Column(String(50), unique=True, index=True, nullable=True) # Para que alumnos se unan
    
    created_at = Column(NaiveDateTime, server_default=func.now(), nullable=False)
    updated_at = Column(NaiveDateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relación muchos a muchos con Profesor
    # Se definirá la tabla de asociación 'profesor_grupo_clase_association' en associations.py
    # y se usará aquí a través del argumento 'secondary'.
    # El back_populates debe coincidir con el nombre de la relación en Profesor.
    profesores = relationship(
        "Profesor",
        secondary=profesor_grupo_clase_association, # Usar el objeto Table importado
        back_populates="grupos_clase"
    )

    # Relación uno-a-muchos con la tabla de asociación GrupoClaseAlumnoAssociation
    # Esto nos permite ver qué alumnos (user_id_hash) están en esta clase y cuándo se unieron.
    alumnos_association = relationship("GrupoClaseAlumnoAssociation", back_populates="grupo_clase")

    # Relación muchos-a-muchos con Curso
    cursos = relationship(
        "Curso",
        secondary=grupo_clase_curso_association,
        back_populates="grupos_clase"
    )

    def __repr__(self):
        return f"<GrupoClase {self.nombre_clase}>" 