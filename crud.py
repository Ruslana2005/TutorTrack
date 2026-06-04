# crud.py
from sqlalchemy.orm import Session
import models, schemas

# ---------- Lessons ----------
def get_lesson(db: Session, lesson_id: int):
    return db.query(models.Lesson).filter(models.Lesson.id == lesson_id).first()

def get_lessons(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Lesson).order_by(models.Lesson.lesson_date.desc(), models.Lesson.start_time.desc()).offset(skip).limit(limit).all()

def create_lesson(db: Session, lesson: schemas.LessonCreate):
    db_lesson = models.Lesson(**lesson.model_dump())
    db.add(db_lesson)
    db.commit()
    db.refresh(db_lesson)
    return db_lesson

def update_lesson(db: Session, lesson_id: int, lesson_update: schemas.LessonUpdate):
    db_lesson = get_lesson(db, lesson_id)
    if not db_lesson:
        return None
    update_data = lesson_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_lesson, key, value)
    db.commit()
    db.refresh(db_lesson)
    return db_lesson

def delete_lesson(db: Session, lesson_id: int):
    db_lesson = get_lesson(db, lesson_id)
    if db_lesson:
        db.delete(db_lesson)
        db.commit()
        return True
    return False

# ---------- Homeworks ----------
def create_homework(db: Session, homework: schemas.HomeworkCreate, lesson_id: int):
    db_homework = models.Homework(**homework.model_dump(), lesson_id=lesson_id)
    db.add(db_homework)
    db.commit()
    db.refresh(db_homework)
    return db_homework

def get_homeworks_by_lesson(db: Session, lesson_id: int):
    return db.query(models.Homework).filter(models.Homework.lesson_id == lesson_id).all()

def delete_homework(db: Session, homework_id: int):
    db_homework = db.query(models.Homework).filter(models.Homework.id == homework_id).first()
    if db_homework:
        db.delete(db_homework)
        db.commit()
        return True
    return False

# ---------- Students ----------
def get_students(db: Session):
    return db.query(models.Student).all()

def create_student(db: Session, student: schemas.StudentCreate):
    db_student = models.Student(**student.model_dump())
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

# ---------- Subjects ----------
def get_subjects(db: Session):
    return db.query(models.Subject).all()

def create_subject(db: Session, subject: schemas.SubjectCreate):
    db_subject = models.Subject(**subject.model_dump())
    db.add(db_subject)
    db.commit()
    db.refresh(db_subject)
    return db_subject