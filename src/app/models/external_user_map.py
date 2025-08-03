from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLAlchemyEnum
from sqlalchemy.sql import func

from app.models.base import Base
from app.models.role_enums import MisuperprofeRole, AreaEnum
# Asumimos que UserProgress está en app.models.user_progress y tiene un campo user_id_hash
# from app.models.user_progress import UserProgress # Se podría necesitar para la relación, pero no para la FK directa si es string

class ExternalUserMap(Base):
    __tablename__ = "external_user_map"

    id = Column(Integer, primary_key=True, index=True)
    external_user_identifier = Column(String, unique=True, index=True, nullable=False)
    # internal_user_id_hash es el identificador único del usuario en Misuperprofe.
    # No se establece un ForeignKey directo a user_progress.user_id_hash en esta etapa
    # para simplificar la migración inicial debido a la PK compuesta de UserProgress.
    # La relación será lógica o definida a nivel de ORM sin FK estricta por ahora.
    internal_user_id_hash = Column(String, unique=True, nullable=True, index=True)
    
    assigned_misuperprofe_role = Column(SQLAlchemyEnum(MisuperprofeRole, name="misuperproferole", create_type=False), nullable=False)
    area = Column(SQLAlchemyEnum(AreaEnum, name="areaenum", create_type=False), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    # La relación user_progress se omite temporalmente del modelo para esta migración inicial.
    # Se puede añadir después si se introduce una tabla User o se define una relación ORM más compleja.

    def __repr__(self):
        return f"<ExternalUserMap(id={self.id}, external_id='{self.external_user_identifier}', role='{self.assigned_misuperprofe_role}')>" 