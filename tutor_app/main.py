# main.py
from fastapi import FastAPI, Depends, HTTPException, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import crud, models, schemas
from database import engine, get_db
from datetime import date, time

# ВАЖНО: НЕ создаём таблицы автоматически, так как они уже есть в БД
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Tutor App")

# Подключаем шаблоны
templates = Jinja2Templates(directory="templates")

# ---------- ГЛАВНАЯ СТРАНИЦА (список уроков) ----------
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, db: Session = Depends(get_db)):
    lessons = crud.get_lessons(db)
    return templates.TemplateResponse("index.html", {"request": request, "lessons": lessons})

# ---------- СТРАНИЦА ДОБАВЛЕНИЯ УРОКА (форма) ----------
@app.get("/lesson/add", response_class=HTMLResponse)
async def add_lesson_form(request: Request, db: Session = Depends(get_db)):
    students = crud.get_students(db)
    subjects = crud.get_subjects(db)
    return templates.TemplateResponse("add_lesson.html", {
        "request": request,
        "students": students,
        "subjects": subjects
    })

# ---------- ОБРАБОТКА ФОРМЫ ДОБАВЛЕНИЯ УРОКА ----------
@app.post("/lesson/add", response_class=HTMLResponse)
async def add_lesson_submit(
    request: Request,
    student_id: int = Form(...),
    subject_id: int = Form(None),
    lesson_date: str = Form(...),
    start_time: str = Form(...),
    end_time: str = Form(None),
    topic: str = Form(None),
    recording_link: str = Form(None),
    notes: str = Form(None),
    db: Session = Depends(get_db)
):
    lesson_date_obj = date.fromisoformat(lesson_date)
    start_time_obj = time.fromisoformat(start_time)
    end_time_obj = time.fromisoformat(end_time) if end_time else None
    
    lesson_data = schemas.LessonCreate(
        student_id=student_id,
        subject_id=subject_id if subject_id and subject_id > 0 else None,
        lesson_date=lesson_date_obj,
        start_time=start_time_obj,
        end_time=end_time_obj,
        topic=topic,
        recording_link=recording_link,
        notes=notes
    )
    crud.create_lesson(db, lesson_data)
    return RedirectResponse(url="/", status_code=303)

# ---------- СТРАНИЦА ДЕТАЛЕЙ УРОКА (с ДЗ и ссылками) ----------
@app.get("/lesson/{lesson_id}", response_class=HTMLResponse)
async def lesson_detail(request: Request, lesson_id: int, db: Session = Depends(get_db)):
    lesson = crud.get_lesson(db, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Урок не найден")
    homeworks = crud.get_homeworks_by_lesson(db, lesson_id)
    students = crud.get_students(db)
    subjects = crud.get_subjects(db)
    return templates.TemplateResponse("lesson_detail.html", {
        "request": request,
        "lesson": lesson,
        "homeworks": homeworks,
        "students": students,
        "subjects": subjects
    })

# ---------- ОБНОВЛЕНИЕ УРОКА ----------
@app.post("/lesson/{lesson_id}/update", response_class=HTMLResponse)
async def update_lesson(
    lesson_id: int,
    student_id: int = Form(...),
    subject_id: int = Form(None),
    lesson_date: str = Form(...),
    start_time: str = Form(...),
    end_time: str = Form(None),
    topic: str = Form(None),
    status: str = Form(None),
    recording_link: str = Form(None),
    notes: str = Form(None),
    db: Session = Depends(get_db)
):
    lesson_date_obj = date.fromisoformat(lesson_date)
    start_time_obj = time.fromisoformat(start_time)
    end_time_obj = time.fromisoformat(end_time) if end_time else None
    
    lesson_update = schemas.LessonUpdate(
        student_id=student_id,
        subject_id=subject_id if subject_id and subject_id > 0 else None,
        lesson_date=lesson_date_obj,
        start_time=start_time_obj,
        end_time=end_time_obj,
        topic=topic,
        status=status,
        recording_link=recording_link,
        notes=notes
    )
    crud.update_lesson(db, lesson_id, lesson_update)
    return RedirectResponse(url=f"/lesson/{lesson_id}", status_code=303)

# ---------- УДАЛЕНИЕ УРОКА ----------
@app.post("/lesson/{lesson_id}/delete")
async def delete_lesson(lesson_id: int, db: Session = Depends(get_db)):
    crud.delete_lesson(db, lesson_id)
    return RedirectResponse(url="/", status_code=303)

# ---------- ДОБАВЛЕНИЕ ДОМАШНЕГО ЗАДАНИЯ ----------
@app.post("/lesson/{lesson_id}/homework/add")
async def add_homework(
    lesson_id: int,
    description: str = Form(...),
    due_date: str = Form(None),
    attached_link: str = Form(None),
    db: Session = Depends(get_db)
):
    due_date_obj = date.fromisoformat(due_date) if due_date else None
    homework_data = schemas.HomeworkCreate(
        description=description,
        due_date=due_date_obj,
        attached_link=attached_link
    )
    crud.create_homework(db, homework_data, lesson_id)
    return RedirectResponse(url=f"/lesson/{lesson_id}", status_code=303)

# ---------- УДАЛЕНИЕ ДОМАШНЕГО ЗАДАНИЯ ----------
@app.post("/homework/{homework_id}/delete")
async def delete_homework(homework_id: int, db: Session = Depends(get_db)):
    homework = db.query(models.Homework).filter(models.Homework.id == homework_id).first()
    lesson_id = homework.lesson_id if homework else None
    crud.delete_homework(db, homework_id)
    return RedirectResponse(url=f"/lesson/{lesson_id}", status_code=303)

# ---------- УПРАВЛЕНИЕ УЧЕНИКАМИ ----------
@app.get("/students", response_class=HTMLResponse)
async def students_list(request: Request, db: Session = Depends(get_db)):
    students = crud.get_students(db)
    return templates.TemplateResponse("students.html", {"request": request, "students": students})

@app.post("/student/add")
async def add_student(
    name: str = Form(...),
    email: str = Form(None),
    phone: str = Form(None),
    db: Session = Depends(get_db)
):
    student_data = schemas.StudentCreate(name=name, email=email, phone=phone)
    crud.create_student(db, student_data)
    return RedirectResponse(url="/students", status_code=303)

# ---------- УПРАВЛЕНИЕ ПРЕДМЕТАМИ ----------
@app.get("/subjects", response_class=HTMLResponse)
async def subjects_list(request: Request, db: Session = Depends(get_db)):
    subjects = crud.get_subjects(db)
    return templates.TemplateResponse("subjects.html", {"request": request, "subjects": subjects})

@app.post("/subject/add")
async def add_subject(
    name: str = Form(...),
    description: str = Form(None),
    db: Session = Depends(get_db)
):
    subject_data = schemas.SubjectCreate(name=name, description=description)
    crud.create_subject(db, subject_data)
    return RedirectResponse(url="/subjects", status_code=303)