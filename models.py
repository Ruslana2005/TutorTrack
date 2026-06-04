# models.py
from sqlalchemy import Column, Integer, String, Text, Date, Time, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
import datetime

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100))
    phone = Column(String(20))
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)

    lessons = relationship("Lesson", back_populates="student")

class Subject(Base):
    __tablename__ = "subjects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)

    lessons = relationship("Lesson", back_populates="subject")

class Lesson(Base):
    __tablename__ = "lessons"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"))
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="SET NULL"))
    lesson_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time)
    topic = Column(String(200))
    status = Column(String(20), default="planned")
    recording_link = Column(Text)
    notes = Column(Text)
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)

    student = relationship("Student", back_populates="lessons")
    subject = relationship("Subject", back_populates="lessons")
    homeworks = relationship("Homework", back_populates="lesson", cascade="all, delete-orphan")

class Homework(Base):
    __tablename__ = "homeworks"
    id = Column(Integer, primary_key=True, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id", ondelete="CASCADE"))
    description = Column(Text, nullable=False)
    due_date = Column(Date)
    attached_link = Column(Text)
    status = Column(String(20), default="assigned")
    submitted_at = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)

    lesson = relationship("Lesson", back_populates="homeworks")