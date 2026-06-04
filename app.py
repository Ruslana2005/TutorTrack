from fastapi import FastAPI, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Text, Date, DateTime, ForeignKey, Table, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from datetime import datetime, date
from typing import Optional, List

# ---------- ФУНКЦИЯ ДЛЯ ИСПРАВЛЕНИЯ КОДИРОВКИ ----------
def fix_encoding(text):
    if not text:
        return text
    try:
        return text.encode('latin1').decode('utf-8')
    except:
        return text

# ---------- НАСТРОЙКА БАЗЫ ДАННЫХ (ПОСТГРЕС) ----------
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:Varenik2005@localhost/mydatabase?client_encoding=utf8"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ---------- ТАБЛИЦА ДЛЯ СВЯЗИ МНОГИЕ-КО-МНОГИМ ----------
student_lesson = Table(
    "student_lesson",
    Base.metadata,
    Column("student_id", Integer, ForeignKey("students.student_id")),
    Column("lesson_id", Integer, ForeignKey("lessons.lesson_id"))
)

# ---------- МОДЕЛИ ----------
class Student(Base):
    __tablename__ = "students"
    student_id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    age = Column(Integer)
    contact_phone = Column(String(255))
    parent_phone = Column(String(255))
    is_tutor = Column(Integer, default=0)
    password = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    lessons = relationship("Lesson", secondary=student_lesson, back_populates="students")
    achievement = relationship("StudentAchievement", back_populates="student", uselist=False)
    exchanges = relationship("Exchange", back_populates="student", cascade="all, delete-orphan")
    grades = relationship("Grade", back_populates="student", cascade="all, delete-orphan")


class Lesson(Base):
    __tablename__ = "lessons"
    lesson_id = Column(Integer, primary_key=True, index=True)
    lesson_date = Column(DateTime, nullable=False)
    lesson_status = Column(String(255), default="Запланирован")
    payment_status = Column(String(255), default="Не оплачен")
    tutor_first_name = Column(String(255), nullable=False)
    tutor_last_name = Column(String(255), nullable=False)
    homework_link = Column(String(255))
    board_link = Column(String(255))
    due_date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)

    homeworks = relationship("Homework", back_populates="lesson", cascade="all, delete-orphan")
    students = relationship("Student", secondary=student_lesson, back_populates="lessons")


class Homework(Base):
    __tablename__ = "homeworks"
    homework_id = Column(Integer, primary_key=True, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.lesson_id", ondelete="CASCADE"))
    assignment_description = Column(Text, nullable=False)
    due_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    lesson = relationship("Lesson", back_populates="homeworks")
    grades = relationship("Grade", back_populates="homework", cascade="all, delete-orphan")


class Grade(Base):
    __tablename__ = "grades"
    grade_id = Column(Integer, primary_key=True, index=True)
    homework_id = Column(Integer, ForeignKey("homeworks.homework_id", ondelete="CASCADE"))
    student_id = Column(Integer, ForeignKey("students.student_id", ondelete="CASCADE"))
    points = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    homework = relationship("Homework", back_populates="grades")
    student = relationship("Student", back_populates="grades")


class StudentAchievement(Base):
    __tablename__ = "student_achievements"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.student_id", ondelete="CASCADE"))
    total_points = Column(Integer, default=0)
    level = Column(String(100), default="Начинающий")
    updated_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="achievement")


class Prize(Base):
    __tablename__ = "prizes"
    prize_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    cost = Column(Integer, nullable=False)
    icon = Column(String(100), default="fa-gift")
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)


class Exchange(Base):
    __tablename__ = "exchanges"
    exchange_id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.student_id", ondelete="CASCADE"))
    prize_id = Column(Integer, ForeignKey("prizes.prize_id", ondelete="CASCADE"))
    status = Column(String(50), default="approved")
    exchanged_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="exchanges")
    prize = relationship("Prize")


# Создаём таблицы
Base.metadata.create_all(bind=engine)

# ---------- НАСТРОЙКА FASTAPI ----------
app = FastAPI(title="TutorTrack")
app.add_middleware(SessionMiddleware, secret_key="tutortrack_secret_key_2025")
templates = Jinja2Templates(directory="templates")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ----------
def get_current_user(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    user = db.query(Student).filter(Student.student_id == user_id).first()
    if user:
        user.first_name = fix_encoding(user.first_name)
        user.last_name = fix_encoding(user.last_name)
    return user


# ---------- ВХОД И ВЫХОД ----------
@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(
    request: Request,
    login_type: Optional[str] = Form(None),
    user_id: Optional[int] = Form(None),
    tutor_password: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    if login_type == "tutor":
        if tutor_password and tutor_password == "tutor123":
            tutor = db.query(Student).filter(Student.is_tutor == 1).first()
            if tutor:
                request.session["user_id"] = tutor.student_id
                request.session["is_tutor"] = True
                return RedirectResponse(url="/", status_code=303)
            else:
                return templates.TemplateResponse("login.html", {"request": request, "error": "Репетитор не найден"})
        else:
            return templates.TemplateResponse("login.html", {"request": request, "error": "Неверный пароль"})
    
    if login_type == "student":
        if user_id:
            student = db.query(Student).filter(Student.student_id == user_id, Student.is_tutor == 0).first()
            if student:
                request.session["user_id"] = student.student_id
                request.session["is_tutor"] = False
                return RedirectResponse(url="/", status_code=303)
            else:
                return templates.TemplateResponse("login.html", {"request": request, "error": "Ученик не найден"})
    
    return templates.TemplateResponse("login.html", {"request": request, "error": "Ошибка входа"})

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)


# ---------- ГЛАВНАЯ СТРАНИЦА ----------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    
    if current_user.is_tutor == 1:
        lessons = db.query(Lesson).order_by(Lesson.lesson_date.desc()).all()
        for lesson in lessons:
            lesson.tutor_first_name = fix_encoding(lesson.tutor_first_name)
            lesson.tutor_last_name = fix_encoding(lesson.tutor_last_name)
            for student in lesson.students:
                student.first_name = fix_encoding(student.first_name)
                student.last_name = fix_encoding(student.last_name)
    else:
        lessons = current_user.lessons
        for lesson in lessons:
            lesson.tutor_first_name = fix_encoding(lesson.tutor_first_name)
            lesson.tutor_last_name = fix_encoding(lesson.tutor_last_name)
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "lessons": lessons,
        "current_user": current_user
    })


# ---------- УПРАВЛЕНИЕ УЧЕНИКАМИ ----------
@app.get("/students", response_class=HTMLResponse)
async def students_list(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if not current_user or current_user.is_tutor != 1:
        return RedirectResponse(url="/", status_code=303)
    
    students = db.query(Student).filter(Student.is_tutor == 0).all()
    for student in students:
        student.first_name = fix_encoding(student.first_name)
        student.last_name = fix_encoding(student.last_name)
    return templates.TemplateResponse("students.html", {
        "request": request,
        "students": students,
        "current_user": current_user
    })

@app.post("/student/add")
async def add_student(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    age: int = Form(None),
    contact_phone: str = Form(None),
    parent_phone: str = Form(None),
    db: Session = Depends(get_db)
):
    current_user = get_current_user(request, db)
    if not current_user or current_user.is_tutor != 1:
        return RedirectResponse(url="/", status_code=303)
    
    student = Student(
        first_name=first_name,
        last_name=last_name,
        age=age,
        contact_phone=contact_phone,
        parent_phone=parent_phone,
        is_tutor=0
    )
    db.add(student)
    db.commit()
    return RedirectResponse(url="/students", status_code=303)

@app.post("/student/delete/{student_id}")
async def delete_student(request: Request, student_id: int, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if not current_user or current_user.is_tutor != 1:
        return RedirectResponse(url="/", status_code=303)
    
    student = db.query(Student).filter(Student.student_id == student_id, Student.is_tutor == 0).first()
    if student:
        db.delete(student)
        db.commit()
    
    return RedirectResponse(url="/students", status_code=303)


# ---------- УПРАВЛЕНИЕ УРОКАМИ ----------
@app.get("/lesson/add", response_class=HTMLResponse)
async def add_lesson_form(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if not current_user or current_user.is_tutor != 1:
        return RedirectResponse(url="/", status_code=303)
    
    students = db.query(Student).filter(Student.is_tutor == 0).all()
    for student in students:
        student.first_name = fix_encoding(student.first_name)
        student.last_name = fix_encoding(student.last_name)
    return templates.TemplateResponse("add_lesson.html", {
        "request": request,
        "students": students,
        "current_user": current_user
    })

@app.post("/lesson/add")
async def add_lesson_submit(
    request: Request,
    lesson_date: str = Form(...),
    lesson_status: str = Form("Запланирован"),
    payment_status: Optional[str] = Form(None),
    tutor_first_name: str = Form(...),
    tutor_last_name: str = Form(...),
    homework_link: Optional[str] = Form(None),
    board_link: Optional[str] = Form(None),
    assignment_description: Optional[str] = Form(None),
    homework_due_date: Optional[str] = Form(None),
    student_ids: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    current_user = get_current_user(request, db)
    if not current_user or current_user.is_tutor != 1:
        return RedirectResponse(url="/", status_code=303)
    
    if not payment_status:
        payment_status = "Не оплачен"
    
    lesson_datetime = datetime.fromisoformat(lesson_date)
    
    lesson = Lesson(
        lesson_date=lesson_datetime,
        lesson_status=lesson_status,
        payment_status=payment_status,
        tutor_first_name=tutor_first_name,
        tutor_last_name=tutor_last_name,
        homework_link=homework_link,
        board_link=board_link,
        due_date=lesson_datetime.date() if lesson_datetime else None
    )
    db.add(lesson)
    db.flush()
    
    if assignment_description or homework_link:
        homework_due = datetime.fromisoformat(homework_due_date) if homework_due_date else None
        homework = Homework(
            lesson_id=lesson.lesson_id,
            assignment_description=assignment_description or "Домашнее задание (ссылка)",
            due_date=homework_due
        )
        db.add(homework)
    
    if student_ids:
        student_ids_list = [int(sid.strip()) for sid in student_ids.split(',') if sid.strip()]
        for student_id in student_ids_list:
            student = db.query(Student).filter(Student.student_id == student_id).first()
            if student:
                lesson.students.append(student)
    
    db.commit()
    return RedirectResponse(url="/", status_code=303)

@app.get("/lesson/{lesson_id}", response_class=HTMLResponse)
async def lesson_detail(request: Request, lesson_id: int, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    
    lesson = db.query(Lesson).filter(Lesson.lesson_id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Урок не найден")
    
    if current_user.is_tutor != 1 and lesson not in current_user.lessons:
        return RedirectResponse(url="/", status_code=303)
    
    lesson.tutor_first_name = fix_encoding(lesson.tutor_first_name)
    lesson.tutor_last_name = fix_encoding(lesson.tutor_last_name)
    for student in lesson.students:
        student.first_name = fix_encoding(student.first_name)
        student.last_name = fix_encoding(student.last_name)
    
    homeworks = db.query(Homework).filter(Homework.lesson_id == lesson_id).all()
    
    # Получаем оценки для каждого домашнего задания и каждого ученика
    homework_points = {}
    for homework in homeworks:
        grades = db.query(Grade).filter(Grade.homework_id == homework.homework_id).all()
        homework_points[homework.homework_id] = {g.student_id: g.points for g in grades}
    
    return templates.TemplateResponse("lesson_detail.html", {
        "request": request,
        "lesson": lesson,
        "homeworks": homeworks,
        "homework_points": homework_points,
        "current_user": current_user
    })


# ---------- РЕДАКТИРОВАНИЕ УРОКА ----------
@app.get("/lesson/{lesson_id}/edit", response_class=HTMLResponse)
async def edit_lesson_form(request: Request, lesson_id: int, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if not current_user or current_user.is_tutor != 1:
        return RedirectResponse(url="/", status_code=303)
    
    lesson = db.query(Lesson).filter(Lesson.lesson_id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Урок не найден")
    
    lesson.tutor_first_name = fix_encoding(lesson.tutor_first_name)
    lesson.tutor_last_name = fix_encoding(lesson.tutor_last_name)
    
    students = db.query(Student).filter(Student.is_tutor == 0).all()
    for student in students:
        student.first_name = fix_encoding(student.first_name)
        student.last_name = fix_encoding(student.last_name)
    
    homeworks = db.query(Homework).filter(Homework.lesson_id == lesson_id).all()
    return templates.TemplateResponse("edit_lesson.html", {
        "request": request,
        "lesson": lesson,
        "students": students,
        "homeworks": homeworks,
        "current_user": current_user
    })

@app.post("/lesson/{lesson_id}/edit")
async def edit_lesson_submit(
    request: Request,
    lesson_id: int,
    lesson_date: str = Form(...),
    lesson_status: str = Form(...),
    payment_status: Optional[str] = Form(None),
    tutor_first_name: str = Form(...),
    tutor_last_name: str = Form(...),
    homework_link: Optional[str] = Form(None),
    board_link: Optional[str] = Form(None),
    assignment_description: Optional[str] = Form(None),
    homework_due_date: Optional[str] = Form(None),
    student_ids: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    current_user = get_current_user(request, db)
    if not current_user or current_user.is_tutor != 1:
        return RedirectResponse(url="/", status_code=303)
    
    lesson = db.query(Lesson).filter(Lesson.lesson_id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Урок не найден")
    
    lesson_datetime = datetime.fromisoformat(lesson_date)
    
    lesson.lesson_date = lesson_datetime
    lesson.lesson_status = lesson_status
    if payment_status:
        lesson.payment_status = payment_status
    lesson.tutor_first_name = tutor_first_name
    lesson.tutor_last_name = tutor_last_name
    lesson.homework_link = homework_link
    lesson.board_link = board_link
    
    if assignment_description:
        homework = db.query(Homework).filter(Homework.lesson_id == lesson_id).first()
        homework_due = datetime.fromisoformat(homework_due_date) if homework_due_date else None
        
        if homework:
            homework.assignment_description = assignment_description
            homework.due_date = homework_due
        else:
            homework = Homework(
                lesson_id=lesson_id,
                assignment_description=assignment_description,
                due_date=homework_due
            )
            db.add(homework)
    
    lesson.students.clear()
    if student_ids:
        student_ids_list = [int(sid.strip()) for sid in student_ids.split(',') if sid.strip()]
        for student_id in student_ids_list:
            student = db.query(Student).filter(Student.student_id == student_id).first()
            if student:
                lesson.students.append(student)
    
    db.commit()
    return RedirectResponse(url=f"/lesson/{lesson_id}", status_code=303)


# ---------- ИЗМЕНЕНИЕ СТАТУСА УРОКА ----------
@app.post("/lesson/{lesson_id}/update_status")
async def update_lesson_status(
    request: Request,
    lesson_id: int,
    lesson_status: str = Form(...),
    db: Session = Depends(get_db)
):
    current_user = get_current_user(request, db)
    if not current_user or current_user.is_tutor != 1:
        return RedirectResponse(url="/", status_code=303)
    
    lesson = db.query(Lesson).filter(Lesson.lesson_id == lesson_id).first()
    if lesson:
        lesson.lesson_status = lesson_status
        db.commit()
    
    return RedirectResponse(url="/", status_code=303)


# ---------- ИЗМЕНЕНИЕ СТАТУСА ОПЛАТЫ ----------
@app.post("/lesson/{lesson_id}/update_payment")
async def update_lesson_payment(
    request: Request,
    lesson_id: int,
    payment_status: str = Form(...),
    db: Session = Depends(get_db)
):
    current_user = get_current_user(request, db)
    if not current_user or current_user.is_tutor != 1:
        return RedirectResponse(url="/", status_code=303)
    
    lesson = db.query(Lesson).filter(Lesson.lesson_id == lesson_id).first()
    if lesson:
        lesson.payment_status = payment_status
        db.commit()
    
    return RedirectResponse(url="/", status_code=303)


# ---------- ДОБАВЛЕНИЕ ДОМАШНЕГО ЗАДАНИЯ ----------
@app.post("/lesson/{lesson_id}/homework/add")
async def add_homework(
    request: Request,
    lesson_id: int,
    assignment_description: Optional[str] = Form(None),
    due_date: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    current_user = get_current_user(request, db)
    if not current_user or current_user.is_tutor != 1:
        return RedirectResponse(url="/", status_code=303)
    
    lesson = db.query(Lesson).filter(Lesson.lesson_id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Урок не найден")
    
    if not assignment_description:
        assignment_description = "Домашнее задание (без описания)"
    
    homework_due = datetime.fromisoformat(due_date) if due_date else None
    
    homework = Homework(
        lesson_id=lesson_id,
        assignment_description=assignment_description,
        due_date=homework_due
    )
    db.add(homework)
    db.commit()
    
    return RedirectResponse(url=f"/lesson/{lesson_id}", status_code=303)


# ---------- ОЦЕНКА ЗА ДОМАШНЕЕ ЗАДАНИЕ (ИНДИВИДУАЛЬНО ДЛЯ УЧЕНИКА) ----------
@app.post("/homework/{homework_id}/grade/{student_id}")
async def grade_homework_for_student(
    request: Request,
    homework_id: int,
    student_id: int,
    points: int = Form(...),
    db: Session = Depends(get_db)
):
    current_user = get_current_user(request, db)
    if not current_user or current_user.is_tutor != 1:
        return RedirectResponse(url="/", status_code=303)
    
    points = min(10, max(0, points))
    
    # Ищем существующую оценку
    grade = db.query(Grade).filter(
        Grade.homework_id == homework_id,
        Grade.student_id == student_id
    ).first()
    
    if grade:
        grade.points = points
        grade.updated_at = datetime.utcnow()
    else:
        grade = Grade(
            homework_id=homework_id,
            student_id=student_id,
            points=points
        )
        db.add(grade)
    
    db.commit()
    
    # Обновляем достижения ученика
    total_points = db.query(func.sum(Grade.points)).filter(Grade.student_id == student_id).scalar() or 0
    
    achievement = db.query(StudentAchievement).filter(StudentAchievement.student_id == student_id).first()
    if not achievement:
        achievement = StudentAchievement(student_id=student_id)
        db.add(achievement)
    
    achievement.total_points = total_points
    
    if total_points >= 300:
        achievement.level = "Гроссмейстер ума"
    elif total_points >= 100:
        achievement.level = "Интеллектуал"
    elif total_points >= 50:
        achievement.level = "Эрудит"
    elif total_points >= 20:
        achievement.level = "Продвинутый"
    else:
        achievement.level = "Начинающий"
    
    achievement.updated_at = datetime.utcnow()
    db.commit()
    
    # Получаем урок для редиректа
    homework = db.query(Homework).filter(Homework.homework_id == homework_id).first()
    return RedirectResponse(url=f"/lesson/{homework.lesson_id}", status_code=303)


# ---------- УДАЛЕНИЕ ДОМАШНЕГО ЗАДАНИЯ ----------
@app.post("/homework/{homework_id}/delete")
async def delete_homework(request: Request, homework_id: int, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if not current_user or current_user.is_tutor != 1:
        return RedirectResponse(url="/", status_code=303)
    
    homework = db.query(Homework).filter(Homework.homework_id == homework_id).first()
    if not homework:
        raise HTTPException(status_code=404, detail="Домашнее задание не найдено")
    
    lesson_id = homework.lesson_id
    db.delete(homework)
    db.commit()
    return RedirectResponse(url=f"/lesson/{lesson_id}", status_code=303)


# ---------- ДОСТИЖЕНИЯ УЧЕНИКА ----------
@app.get("/achievements", response_class=HTMLResponse)
async def achievements(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if not current_user or current_user.is_tutor == 1:
        return RedirectResponse(url="/", status_code=303)
    
    # Получаем все оценки ученика через таблицу Grade
    grades = db.query(Grade).filter(Grade.student_id == current_user.student_id).all()
    total_points = sum(g.points or 0 for g in grades)
    
    # Получаем домашние задания с оценками для отображения истории
    homeworks_with_grades = db.query(Homework).join(Grade).filter(Grade.student_id == current_user.student_id).all()
    
    levels = [
        {"name": "Начинающий", "required": 0, "icon": "🌱", "achieved": total_points >= 0},
        {"name": "Продвинутый", "required": 20, "icon": "🍃", "achieved": total_points >= 20},
        {"name": "Эрудит", "required": 50, "icon": "🧠", "achieved": total_points >= 50},
        {"name": "Интеллектуал", "required": 100, "icon": "🎓", "achieved": total_points >= 100},
        {"name": "Гроссмейстер ума", "required": 300, "icon": "👑", "achieved": total_points >= 300},
    ]
    
    next_level = None
    for level in levels:
        if not level["achieved"]:
            next_level = level
            break
    
    next_level_required = next_level["required"] if next_level else 0
    next_level_name = next_level["name"] if next_level else "Максимум"
    
    if next_level and total_points < next_level_required:
        prev_required = levels[levels.index(next_level) - 1]["required"]
        progress_percent = ((total_points - prev_required) / (next_level_required - prev_required)) * 100
    else:
        progress_percent = 100
    
    return templates.TemplateResponse("achievements.html", {
        "request": request,
        "current_user": current_user,
        "total_points": total_points,
        "homeworks": homeworks_with_grades,
        "levels": levels,
        "next_level_required": next_level_required,
        "next_level_name": next_level_name,
        "progress_percent": min(100, max(0, progress_percent))
    })


# ---------- ЛАВКА (МАГАЗИН ПРИЗОВ) ----------
@app.get("/shop", response_class=HTMLResponse)
async def shop(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if not current_user or current_user.is_tutor == 1:
        return RedirectResponse(url="/", status_code=303)
    
    total_points = db.query(func.sum(Grade.points)).filter(Grade.student_id == current_user.student_id).scalar() or 0
    
    exchanges = db.query(Exchange).filter(Exchange.student_id == current_user.student_id).all()
    exchanged_prize_ids = [e.prize_id for e in exchanges]
    
    has_exchanged_100 = any(e.prize_id in [8, 9] for e in exchanges)
    has_exchanged_500 = any(e.prize_id in [11, 12] for e in exchanges)
    
    return templates.TemplateResponse("shop.html", {
        "request": request,
        "current_user": current_user,
        "total_points": total_points,
        "exchanged_prize_ids": exchanged_prize_ids,
        "has_exchanged_100": has_exchanged_100,
        "has_exchanged_500": has_exchanged_500
    })


@app.post("/shop/exchange/7")
async def exchange_prize_7(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if not current_user or current_user.is_tutor == 1:
        return RedirectResponse(url="/", status_code=303)
    
    total_points = db.query(func.sum(Grade.points)).filter(Grade.student_id == current_user.student_id).scalar() or 0
    
    if total_points < 50:
        return RedirectResponse(url="/shop?error=Недостаточно кубков", status_code=303)
    
    existing = db.query(Exchange).filter(
        Exchange.student_id == current_user.student_id,
        Exchange.prize_id == 7
    ).first()
    
    if existing:
        return RedirectResponse(url="/shop?error=Вы уже обменивали этот приз", status_code=303)
    
    exchange = Exchange(student_id=current_user.student_id, prize_id=7, status='approved')
    db.add(exchange)
    db.commit()
    
    return RedirectResponse(url="/shop", status_code=303)


@app.post("/shop/exchange/10")
async def exchange_prize_10(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if not current_user or current_user.is_tutor == 1:
        return RedirectResponse(url="/", status_code=303)
    
    total_points = db.query(func.sum(Grade.points)).filter(Grade.student_id == current_user.student_id).scalar() or 0
    
    if total_points < 300:
        return RedirectResponse(url="/shop?error=Недостаточно кубков", status_code=303)
    
    existing = db.query(Exchange).filter(
        Exchange.student_id == current_user.student_id,
        Exchange.prize_id == 10
    ).first()
    
    if existing:
        return RedirectResponse(url="/shop?error=Вы уже обменивали этот приз", status_code=303)
    
    exchange = Exchange(student_id=current_user.student_id, prize_id=10, status='approved')
    db.add(exchange)
    db.commit()
    
    return RedirectResponse(url="/shop", status_code=303)


@app.post("/shop/exchange/100_choice")
async def exchange_100_choice(request: Request, prize_choice: str = Form(...), db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if not current_user or current_user.is_tutor == 1:
        return RedirectResponse(url="/", status_code=303)
    
    total_points = db.query(func.sum(Grade.points)).filter(Grade.student_id == current_user.student_id).scalar() or 0
    
    if total_points < 100:
        return RedirectResponse(url="/shop?error=Недостаточно кубков", status_code=303)
    
    existing = db.query(Exchange).filter(
        Exchange.student_id == current_user.student_id,
        Exchange.prize_id.in_([8, 9])
    ).first()
    
    if existing:
        return RedirectResponse(url="/shop?error=Вы уже обменивали приз за 100 кубков", status_code=303)
    
    prize_id = 8 if prize_choice == "ozon" else 9
    
    exchange = Exchange(student_id=current_user.student_id, prize_id=prize_id, status='approved')
    db.add(exchange)
    db.commit()
    
    return RedirectResponse(url="/shop", status_code=303)


@app.post("/shop/exchange/500_choice")
async def exchange_500_choice(request: Request, prize_choice: str = Form(...), db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if not current_user or current_user.is_tutor == 1:
        return RedirectResponse(url="/", status_code=303)
    
    total_points = db.query(func.sum(Grade.points)).filter(Grade.student_id == current_user.student_id).scalar() or 0
    
    if total_points < 500:
        return RedirectResponse(url="/shop?error=Недостаточно кубков", status_code=303)
    
    existing = db.query(Exchange).filter(
        Exchange.student_id == current_user.student_id,
        Exchange.prize_id.in_([11, 12])
    ).first()
    
    if existing:
        return RedirectResponse(url="/shop?error=Вы уже обменивали приз за 500 кубков", status_code=303)
    
    prize_id = 11 if prize_choice == "apple500" else 12
    
    exchange = Exchange(student_id=current_user.student_id, prize_id=prize_id, status='approved')
    db.add(exchange)
    db.commit()
    
    return RedirectResponse(url="/shop", status_code=303)


# ---------- API ДЛЯ СТАТИСТИКИ ----------
@app.get("/api/stats")
async def api_stats(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if not current_user or current_user.is_tutor != 1:
        return {"error": "Доступ запрещён"}
    
    students_count = db.query(Student).filter(Student.is_tutor == 0).count()
    lessons_count = db.query(Lesson).count()
    homeworks_count = db.query(Homework).count()
    paid_count = db.query(Lesson).filter(Lesson.payment_status == "Оплачен").count()
    
    return {
        "students_count": students_count,
        "lessons_count": lessons_count,
        "homeworks_count": homeworks_count,
        "paid_count": paid_count
    }


# ---------- УДАЛЕНИЕ УРОКА ----------
@app.post("/lesson/{lesson_id}/delete")
async def delete_lesson(request: Request, lesson_id: int, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if not current_user or current_user.is_tutor != 1:
        return RedirectResponse(url="/", status_code=303)
    
    lesson = db.query(Lesson).filter(Lesson.lesson_id == lesson_id).first()
    if lesson:
        db.delete(lesson)
        db.commit()
    
    return RedirectResponse(url="/", status_code=303)