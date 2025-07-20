from typing import List, Optional
from pydantic import BaseModel
from app.models.adaptive import UserChapterStatus

class UserProgressState(BaseModel):
    status: UserChapterStatus
    porcentaje_avance: int
    puede_iniciar_o_continuar: bool

class ChapterWithProgress(BaseModel):
    chapter_id: str
    title: str
    order: Optional[int] = None
    estado_usuario: UserProgressState
    class Config:
        from_attributes = True

class CourseChapterListResponse(BaseModel):
    course_name: str
    chapters: List[ChapterWithProgress]
    total: int
    page: int
    page_size: int
    has_next: bool

class ChapterBasicInfo(BaseModel):
    chapter_id: int
    title: str
    order: Optional[int] = None

    class Config:
        from_attributes = True

class CourseChapterBasicListResponse(BaseModel):
    course_id: int
    course_name: str
    chapters: List[ChapterBasicInfo]
    total: int
    page: int
    page_size: int
    has_next: bool 