from sqlalchemy import Column, String, Integer, DateTime, Numeric, Boolean, ForeignKey, PrimaryKeyConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from datetime import datetime
from app.models.base import Base
import uuid
from app.db.custom_types import NaiveDateTime
import enum
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship

class LessonSession(Base):
    __tablename__ = "lesson_sessions"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id_hash = Column(String(64), nullable=False, index=True)
    course = Column(String(64), nullable=False, index=True)
    topic = Column(String(200))
    chapter_id = Column(Integer, ForeignKey("capitulo.id"))
    started_at = Column(NaiveDateTime, default=lambda: datetime.utcnow())
    ended_at = Column(NaiveDateTime)
    lesson_xp = Column(Integer, default=0)
    accuracy = Column(Numeric(4,3))
    items_completed = Column(Integer, default=0)
    difficulty_level = Column(Numeric)
    current_session_streak = Column(Integer, default=0, nullable=False, server_default="0")

class UserProgress(Base):
    __tablename__ = "user_progress"
    user_id_hash = Column(String(64), primary_key=True)
    course = Column(String(64), primary_key=True)
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    total_xp = Column(Integer, default=0)
    last_active = Column(NaiveDateTime, default=lambda: datetime.utcnow())
    hearts = Column(Integer, default=5)  # Vidas
    chests = Column(Integer, default=0)  # Cofres
    achievements = Column(String(512), default="")  # Logros serializados (CSV o JSON)
    theta = Column(Numeric(5,3), nullable=False, default=0.0, server_default="0.0")  # Parámetro IRT

    # La relación external_map_entry se omite temporalmente para esta migración inicial.

class Streak(Base):
    __tablename__ = "streaks"
    user_id_hash = Column(String(64), primary_key=True)
    current_days = Column(Integer, default=0)
    longest_days = Column(Integer, default=0)
    last_active = Column(NaiveDateTime, default=lambda: datetime.utcnow())

class LessonError(Base):
    __tablename__ = "errors"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(PG_UUID(as_uuid=True), ForeignKey("lesson_sessions.id"), nullable=False, index=True)
    course = Column(String(64), nullable=True)
    item_id = Column(String(64), nullable=False)
    resolved = Column(Boolean, default=False)
    created_at = Column(NaiveDateTime, default=lambda: datetime.utcnow())

class UserChapterStatus(str, enum.Enum):
    NO_INICIADO = "no_iniciado"
    EN_PROGRESO = "en_progreso"
    COMPLETADO = "completado"

class ProgressUnit(Base):
    __tablename__ = "progress_units"
    user_id_hash = Column(String(64), primary_key=True)
    course = Column(String(64), nullable=True)
    chapter_id = Column(Integer, ForeignKey("capitulo.id"), primary_key=True)
    state = Column(SQLAlchemyEnum(UserChapterStatus, name="userchapterstatus", create_type=False), default=UserChapterStatus.NO_INICIADO)
    porcentaje = Column(Integer, default=0)
    stars = Column(Integer, default=0)

    capitulo = relationship("Capitulo", back_populates="progress_units")

class GrowthLog(Base):
    __tablename__ = "growth_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id_hash = Column(String(64), nullable=False, index=True)
    prompt_type = Column(String(32), nullable=False, index=True)
    shown_at = Column(NaiveDateTime, default=lambda: datetime.utcnow())
    action = Column(String(16))  # ACCEPT, DECLINE, IGNORE
    cooldown_until = Column(NaiveDateTime)

class SpacedRepetition(Base):
    __tablename__ = "spaced_repetition"
    user_id_hash = Column(String(64), primary_key=True)
    course = Column(String(64), nullable=True)
    item_id = Column(Integer, ForeignKey("capitulo.id"), primary_key=True)
    last_seen = Column(NaiveDateTime, default=lambda: datetime.utcnow())
    times_seen = Column(Integer, default=1)
    times_correct = Column(Integer, default=0)
    times_incorrect = Column(Integer, default=0)
    easiness_factor = Column(Numeric(4, 2), default=2.5, nullable=False, server_default="2.5")
    repetition_number = Column(Integer, default=0, nullable=False, server_default="0")
    current_interval_days = Column(Integer, default=0, nullable=False, server_default="0")
    next_due = Column(NaiveDateTime, default=lambda: datetime.utcnow())
    difficulty = Column(String(16), default="normal")
    __table_args__ = (
        PrimaryKeyConstraint('user_id_hash', 'item_id', name='pk_spaced_repetition'),
    ) 

class AchievementsLog(Base):
    __tablename__ = "achievements_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id_hash = Column(String(64), nullable=False, index=True)
    achievement_type = Column(String(64), nullable=False)
    unlocked_at = Column(NaiveDateTime, default=lambda: datetime.utcnow())
    details = Column(String(256))

class Attempt(Base):
    __tablename__ = "attempts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id_hash = Column(String(64), nullable=False, index=True)
    question_id = Column(String(64), nullable=False)  # Almacena el item_id (chapter_id) como string
    answer = Column(String, nullable=True)  # Respuesta textual del estudiante
    is_correct = Column(Boolean, nullable=False)
    course = Column(String(64), nullable=False)
    topic = Column(String(200), nullable=True)  # Título del capítulo/item
    created_at = Column(NaiveDateTime, default=lambda: datetime.utcnow(), nullable=False)

    def __repr__(self) -> str:
        return f"<Attempt {self.id} - User: {self.user_id_hash} Q: {self.question_id}>" 