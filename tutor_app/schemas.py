# schemas.py
from pydantic import BaseModel
from datetime import date, time, datetime
from typing import Optional

# Students
class StudentBase(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None

class StudentCreate(StudentBase):
    pass

class Student(StudentBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

# Subjects
class SubjectBase(BaseModel):
    name: str
    description: Optional[str] = None

class SubjectCreate(SubjectBase):
    pass

class Subject(SubjectBase):
    id: int
    class Config:
        from_attributes = True

# Homeworks
class HomeworkBase(BaseModel):
    description: str
    due_date: Optional[date] = None
    attached_link: Optional[str] = None
    status: Optional[str] = "assigned"

class HomeworkCreate(HomeworkBase):
    pass

class Homework(HomeworkBase):
    id: int
    lesson_id: int
    created_at: datetime
    submitted_at: Optional[datetime] = None
    class Config:
        from_attributes = True

# Lessons
class LessonBase(BaseModel):
    student_id: int
    subject_id: Optional[int] = None
    lesson_date: date
    start_time: time
    end_time: Optional[time] = None
    topic: Optional[str] = None
    status: Optional[str] = "planned"
    recording_link: Optional[str] = None
    notes: Optional[str] = None

class LessonCreate(LessonBase):
    pass

class LessonUpdate(BaseModel):
    student_id: Optional[int] = None
    subject_id: Optional[int] = None
    lesson_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    topic: Optional[str] = None
    status: Optional[str] = None
    recording_link: Optional[str] = None
    notes: Optional[str] = None

class Lesson(LessonBase):
    id: int
    created_at: datetime
    student: Optional[Student] = None
    subject: Optional[Subject] = None
    homeworks: list[Homework] = []
    class Config:
        from_attributes = True