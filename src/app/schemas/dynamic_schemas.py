from pydantic import BaseModel, Field
from typing import List, Optional

class ProgressByCourse(BaseModel):
    """Schema for progress aggregated by course."""
    course: str = Field(..., description="Name of the course")
    xp: int = Field(..., description="Total XP earned in this course")
    questions_answered: int = Field(..., description="Total questions answered in this course")
    correct_answers: int = Field(..., description="Total correct answers in this course")

class UserProgressData(BaseModel):
    """Data part of the user progress response."""
    user_id: str = Field(..., description="User's unique identifier")
    total_xp: int = Field(..., description="Total XP across all courses")
    current_streak: int = Field(..., description="Current daily streak")
    total_questions_answered: int = Field(..., description="Total questions answered across all courses")
    correct_answers: int = Field(..., description="Total correct answers across all courses")
    progress_by_course: List[ProgressByCourse] = Field(..., description="Detailed progress for each course attempted")

class UserProgressResponse(BaseModel):
    """Response schema for the get_progress action."""
    success: bool = Field(..., description="Indicates if the request was successful")
    data: UserProgressData = Field(..., description="The user's progress data")
    message: str = Field(..., description="A message describing the result") 