from sqlalchemy import Column, Integer, String, DateTime, Boolean, UniqueConstraint
from datetime import datetime
from .base import Base

class TeacherRole(Base):
    __tablename__ = "teacher_roles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), unique=True, nullable=False, index=True)
    role_type = Column(String(50), nullable=False, default="student")  # student, teacher, admin
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class StudentAssignment(Base):
    __tablename__ = "student_assignments"

    id = Column(Integer, primary_key=True, index=True)
    teacher_user_id = Column(String(255), nullable=False, index=True)
    student_user_id = Column(String(255), nullable=False, index=True)
    assigned_date = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    __table_args__ = (UniqueConstraint('teacher_user_id', 'student_user_id', name='unique_teacher_student'),) 