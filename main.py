from fastapi import FastAPI, HTTPException, Query, Depends, File, UploadFile, Request, Body, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import or_, text, and_
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from jose import JWTError, jwt
import uvicorn
import os
import io
import uuid
import random
import gzip
import string
from dotenv import load_dotenv
import json
from pathlib import Path
from auth import get_current_admin

load_dotenv()
from sqlalchemy.orm.attributes import flag_modified
from models import Base, User, Project, ProjectFile, Invitation
from database import engine, session_local
from schemas import (
    StudentCreate, StudentResponse, StudentUpdate,
    TeacherCreate, TeacherResponse, TeacherUpdate, TeacherInfo,
    UserResponse, LoginRequest,
    ProjectRole, Participant, ProjectCreate, ProjectResponse, ProjectUpdate, Comment,
    EmailVerificationCodeRequest, EmailVerificationRequest,
    PasswordResetRequest, PasswordResetConfirm,
    TokenResponse,
    Suggestion, SuggestionCreate, SuggestionStatus,
    InvitationCreate, InvitationInfo,
    ProjectFileResponse, InvitationResponse,
    RequiredFile, TaskTemplate
)

from willow import Image
from PIL import Image as PILImage
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig

from auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    get_current_user,
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    oauth2_scheme
)

from fastapi.security import OAuth2PasswordRequestFormStrict
from email_utils import generate_verification_code, send_verification_email, send_password_reset_email
from core.memory_store import memory_store as redis_client

app = FastAPI(title="School Platform API", description="API для управления учениками, учителями и проектами")
ADMIN_INIT_PASSWORD = os.getenv("ADMIN_INIT_PASSWORD", "SuperMegaSilvaAdmin")
DEFAULT_TASKS_FILE = "default_tasks.json"
FILE_SIZE_LIMITS_FILE = "file_size_limits.json"

# Настройка CORS
origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

os.makedirs("avatars", exist_ok=True)
os.makedirs("uploads", exist_ok=True)
app.mount("/avatars", StaticFiles(directory="avatars"), name="avatars")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
AVATAR_DIR = "avatars"

Base.metadata.create_all(bind=engine)

def get_db():
    db = session_local()
    try:
        yield db
    finally:
        db.close()

def is_curator(user: User) -> bool:
    return user.is_teacher and user.teacher_info and user.teacher_info.get("curator", False)

def get_author_role(user: User, project: Project) -> str:
    if user.is_admin:
        return "Администратор"
    if is_curator(user):
        return "Куратор"
    for p in (project.participants or []):
        if p.get("user_id") == user.id:
            role = p.get("role")
            role_names = {
                "customer": "Заказчик",
                "supervisor": "Научный руководитель",
                "expert": "Эксперт",
                "executor": "Исполнитель",
                "curator": "Куратор (в проекте)"
            }
            return role_names.get(role, role)
    return "Участник"

def load_default_tasks() -> Dict[str, Any]:
    if not os.path.exists(DEFAULT_TASKS_FILE):
        initial = {
            "8": {"label": "8 класс", "tasks": []},
            "10": {"label": "10 класс", "directions": {}},
            "11": {"label": "11 класс", "directions": {}}
        }
        with open(DEFAULT_TASKS_FILE, "w", encoding="utf-8") as f:
            json.dump(initial, f, ensure_ascii=False, indent=2)
        return initial
    with open(DEFAULT_TASKS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_default_tasks(data: Dict[str, Any]):
    with open(DEFAULT_TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_file_limits():
    if not os.path.exists(FILE_SIZE_LIMITS_FILE):
        default_limits = {
            "text/plain": 5 * 1024 * 1024,
            "application/pdf": 5 * 1024 * 1024,
            "application/msword": 5 * 1024 * 1024,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": 5 * 1024 * 1024,
            "application/vnd.ms-powerpoint": 30 * 1024 * 1024,
            "application/vnd.openxmlformats-officedocument.presentationml.presentation": 30 * 1024 * 1024,
            "image/png": 10 * 1024 * 1024,
            "image/jpeg": 10 * 1024 * 1024,
            "image/x-icon": 1 * 1024 * 1024,
            "image/vnd.microsoft.icon": 1 * 1024 * 1024,
            "audio/mpeg": 10 * 1024 * 1024,
            "video/mp4": 50 * 1024 * 1024,
        }
        with open(FILE_SIZE_LIMITS_FILE, "w", encoding="utf-8") as f:
            json.dump(default_limits, f, indent=2)
        return default_limits
    with open(FILE_SIZE_LIMITS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_file_limits(data: dict):
    with open(FILE_SIZE_LIMITS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# Новая зависимость: авторизация через query-параметр или заголовок
async def get_user_from_query_or_header(
    request: Request,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
) -> User:
    """Пытается получить пользователя из query-параметра ?token=, иначе из заголовка Authorization."""
    if token:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid token payload")
            user = db.query(User).get(int(user_id))
            if not user:
                raise HTTPException(status_code=401, detail="User not found")
            return user
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
    else:
        authorization = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Not authenticated")
        token = authorization.split("Bearer ")[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid token payload")
            user = db.query(User).get(int(user_id))
            if not user:
                raise HTTPException(status_code=401, detail="User not found")
            return user
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

# ==================== ЭНД ТОКЕНОВ ====================
@app.post("/token", response_model=TokenResponse, tags=["Auth"])
async def token_login(
    form_data: OAuth2PasswordRequestFormStrict = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        (User.nickname == form_data.username.strip()) |
        (User.email == form_data.username.strip())
    ).first()
    if not user:
        raise HTTPException(status_code=402, detail="Пользователь с таким логином не найден")
    if not verify_password(form_data.password.strip(), user.password):
        raise HTTPException(status_code=402, detail="Неверный пароль")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Пользователь забанен")
    access_token = create_access_token({"sub": str(user.id), "is_teacher": user.is_teacher})
    refresh_token = create_refresh_token({"sub": str(user.id), "is_teacher": user.is_teacher})
    redis_client.setex(f"refresh:{user.id}:{refresh_token}", REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60, "valid")
    return TokenResponse(access_token=access_token, refresh_token=refresh_token, token_type="bearer")

# ==================== ЭНД АДМИНОВ ====================
@app.patch("/admin/projects/{project_id}/toggle-file-limits", response_model=ProjectResponse, tags=["Admin"])
async def toggle_project_file_limits(
    project_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project.ignore_file_limits = not project.ignore_file_limits
    db.commit()
    db.refresh(project)
    return project

@app.get("/admin/file-size-limits", tags=["Admin"])
async def get_file_size_limits(admin: User = Depends(get_current_admin)):
    return load_file_limits()

@app.put("/admin/file-size-limits", tags=["Admin"])
async def update_file_size_limits(
    data: Dict[str, int] = Body(...),
    admin: User = Depends(get_current_admin)
):
    save_file_limits(data)
    return {"message": "File size limits updated"}

@app.post("/admin/users", response_model=UserResponse, tags=["Admin"])
async def admin_create_user(
    username: str = Body(..., description="Никнейм нового администратора"),
    password: str = Body(..., description="Пароль нового администратора"),
    fullname: str = Body(..., description="Полное имя"),
    email: str = Body(..., description="Email"),
    master_password: str = Body(..., description="Мастер-пароль для создания администратора"),
    db: Session = Depends(get_db)
):
    if master_password != ADMIN_INIT_PASSWORD:
        raise HTTPException(status_code=403, detail="Invalid master password")
    existing_nickname = db.query(User).filter(User.nickname == username.strip()).first()
    if existing_nickname:
        raise HTTPException(status_code=400, detail="Nickname already exists")
    existing_email = db.query(User).filter(User.email == email.strip()).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already exists")
    hashed = get_password_hash(password.strip())
    new_user = User(
        nickname=username.strip(),
        fullname=fullname,
        email=email.strip(),
        password=hashed,
        is_active=True,
        is_verified=True,
        is_teacher=False,
        is_admin=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.delete("/admin/comments/{comment_id}", tags=["Admin"])
async def admin_delete_comment_permanently(
    comment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not (current_user.is_admin or is_curator(current_user)):
        raise HTTPException(status_code=403, detail="Only admin or curator can permanently delete comments")
    projects = db.query(Project).all()
    found = False
    for project in projects:
        if project.comments:
            for i, c in enumerate(project.comments):
                if c.get("id") == comment_id and c.get("hidden") == True:
                    project.comments.pop(i)
                    flag_modified(project, "comments")
                    db.commit()
                    found = True
                    break
        if found:
            break
        if project.tasks:
            for task in project.tasks:
                if task.get("comments"):
                    for j, c in enumerate(task["comments"]):
                        if c.get("id") == comment_id and c.get("hidden") == True:
                            task["comments"].pop(j)
                            flag_modified(project, "tasks")
                            db.commit()
                            found = True
                            break
                    if found:
                        break
            if found:
                break
    if not found:
        raise HTTPException(status_code=404, detail="Hidden comment not found")
    return {"message": "Comment permanently deleted"}

@app.get("/admin/users", response_model=List[UserResponse], tags=["Admin"])
async def admin_get_all_users(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    return db.query(User).all()

@app.get("/admin/users/{user_id}", response_model=UserResponse, tags=["Admin"])
async def admin_get_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    return user

@app.put("/admin/users/{user_id}", response_model=UserResponse, tags=["Admin"])
async def admin_update_user(
    user_id: int,
    user_update: dict,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    allowed_fields = {"fullname", "email", "is_active", "is_verified", "is_admin", "is_teacher", "teacher_info"}
    for field, value in user_update.items():
        if field in allowed_fields:
            setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user

@app.delete("/admin/users/{user_id}", tags=["Admin"])
async def admin_delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    if user.avatar:
        filepath = os.path.join(AVATAR_DIR, user.avatar)
        if os.path.exists(filepath):
            os.remove(filepath)
    all_projects = db.query(Project).all()
    for p in all_projects:
        if p.participants:
            p.participants = [part for part in p.participants if part.get("user_id") != user_id]
    db.delete(user)
    db.commit()
    return {"message": f"User {user_id} deleted"}

@app.post("/admin/users/delete-all", tags=["Admin"])
async def admin_delete_all_users(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    users = db.query(User).all()
    for user in users:
        if user.avatar:
            filepath = os.path.join(AVATAR_DIR, user.avatar)
            if os.path.exists(filepath):
                os.remove(filepath)
    db.query(User).delete()
    db.commit()
    return {"message": "All users deleted"}

@app.get("/admin/projects", response_model=List[ProjectResponse], tags=["Admin"])
async def admin_get_all_projects(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    return db.query(Project).all()

@app.get("/admin/projects/{project_id}", response_model=ProjectResponse, tags=["Admin"])
async def admin_get_project(
    project_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    return project

@app.put("/admin/projects/{project_id}", response_model=ProjectResponse, tags=["Admin"])
async def admin_update_project(
    project_id: int,
    project_update: ProjectUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    update_data = project_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(project, field):
            setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return project

@app.delete("/admin/projects/{project_id}", tags=["Admin"])
async def admin_delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    db.delete(project)
    db.commit()
    return {"message": f"Project {project_id} deleted"}

@app.post("/admin/projects/delete-all", tags=["Admin"])
async def admin_delete_all_projects(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    db.query(Project).delete()
    db.commit()
    return {"message": "All projects deleted"}

@app.get("/admin/teachers", response_model=List[UserResponse], tags=["Admin"])
async def admin_get_teachers(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    return db.query(User).filter(User.is_teacher == True).all()

@app.put("/admin/teachers/{user_id}/curator", tags=["Admin"])
async def admin_set_curator(
    user_id: int,
    is_curator: bool,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    user = db.query(User).filter(User.id == user_id, User.is_teacher == True).first()
    if not user:
        raise HTTPException(404, "Teacher not found")
    if not user.teacher_info:
        user.teacher_info = {}
    user.teacher_info["curator"] = is_curator
    db.commit()
    return {"message": f"Curator status for user {user_id} set to {is_curator}"}

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ ПРОЕКТОВ ====================
def is_project_participant(project: Project, user_id: int) -> bool:
    return any(p.get("user_id") == user_id for p in (project.participants or []))

def get_participant_role(project: Project, user_id: int) -> Optional[str]:
    for p in (project.participants or []):
        if p.get("user_id") == user_id:
            return p.get("role")
    return None

# ==================== ВЕРИФИКАЦИЯ EMAIL УЧИТЕЛЯ ====================
ACCEPTED_EMAILS_FILE = Path("accepted_emails.json")

def load_accepted_emails():
    if not ACCEPTED_EMAILS_FILE.exists():
        example_emails = {
            "accepted_emails": ["teacher@school.ru", "professor@university.ru", "учитель@школа.рф"],
            "domains": ["school.ru", "education.ru", "teacher.org"]
        }
        with open(ACCEPTED_EMAILS_FILE, 'w', encoding='utf-8') as f:
            json.dump(example_emails, f, ensure_ascii=False, indent=2)
        return example_emails
    try:
        with open(ACCEPTED_EMAILS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Ошибка загрузки файла с email: {e}")
        return {"accepted_emails": [], "domains": []}

def is_email_accepted(email: str) -> bool:
    data = load_accepted_emails()
    email_lower = email.lower()
    if email_lower in [e.lower() for e in data.get("accepted_emails", [])]:
        return True
    domain = email_lower.split('@')[-1]
    if domain in [d.lower() for d in data.get("domains", [])]:
        return True
    return False

# ==================== ВЕРИФИКАЦИЯ EMAIL УЧЕНИКА ====================
ACCEPTED_STUDENT_EMAILS_FILE = Path("accepted_student_emails.json")

def load_accepted_student_emails():
    if not ACCEPTED_STUDENT_EMAILS_FILE.exists():
        example_emails = {
            "accepted_emails": [],
            "domains": ["lit1533.ru"]
        }
        with open(ACCEPTED_STUDENT_EMAILS_FILE, 'w', encoding='utf-8') as f:
            json.dump(example_emails, f, ensure_ascii=False, indent=2)
        return example_emails
    try:
        with open(ACCEPTED_STUDENT_EMAILS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Ошибка загрузки файла с email учеников: {e}")
        return {"accepted_emails": [], "domains": []}

def is_student_email_accepted(email: str) -> bool:
    data = load_accepted_student_emails()
    email_lower = email.lower()
    domain = email_lower.split('@')[-1]
    allowed_domains = [d.lower() for d in data.get("domains", [])]
    if domain in allowed_domains:
        return True
    if email_lower in [e.lower() for e in data.get("accepted_emails", [])]:
        return True
    return False

@app.post("/auth/check-student-email", tags=["Auth"])
async def check_student_email(request: dict):
    email = request.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    if is_student_email_accepted(email):
        return {"accepted": True, "message": "Email разрешён для регистрации ученика"}
    else:
        raise HTTPException(
            status_code=403,
            detail="Этот email не разрешён для регистрации ученика. Используйте email с доменом lit1533.ru или из списка разрешённых."
        )

# ==================== УЧЕНИКИ ====================
@app.get("/default-tasks", tags=["DefaultTasks"])
async def get_default_tasks(current_user: User = Depends(get_current_user)):
    return load_default_tasks()

@app.post("/students/", response_model=StudentResponse, tags=["Students"])
async def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    existing_nickname = db.query(User).filter(User.nickname == student.nickname.strip()).first()
    if existing_nickname:
        raise HTTPException(status_code=400, detail="Пользователь с таким никнеймом уже существует")
    existing_email = db.query(User).filter(User.email == student.email.strip()).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")
    hashed_password = get_password_hash(student.password.strip())
    db_user = User(
        nickname=student.nickname.strip(),
        fullname=student.fullname,
        class_=student.class_,
        speciality=student.speciality,
        email=student.email.strip(),
        password=hashed_password,
        avatar=None,
        is_active=True,
        is_verified=False,
        is_teacher=False,
        teacher_info=None
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/students/", response_model=List[StudentResponse], tags=["Students"])
async def get_students(q: Optional[str] = Query(None), db: Session = Depends(get_db)):
    query = db.query(User).filter(User.is_teacher == False)
    if q:
        query = query.filter(or_(User.nickname.ilike(f"%{q}%"), User.fullname.ilike(f"%{q}%"), User.email.ilike(f"%{q}%")))
    return query.all()

@app.get("/students/{student_id}", response_model=StudentResponse, tags=["Students"])
async def get_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(User).filter(User.id == student_id, User.is_teacher == False).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

@app.put("/students/{student_id}", response_model=StudentResponse, tags=["Students"])
async def update_student(student_id: int, student_update: StudentUpdate, db: Session = Depends(get_db)):
    student = db.query(User).filter(User.id == student_id, User.is_teacher == False).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    if student_update.fullname is not None:
        student.fullname = student_update.fullname
    if student_update.email is not None:
        existing = db.query(User).filter(User.email == student_update.email, User.id != student_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
        student.email = student_update.email
    if student_update.class_ is not None:
        student.class_ = student_update.class_
    if student_update.speciality is not None:
        student.speciality = student_update.speciality
    db.commit()
    db.refresh(student)
    return student

@app.delete("/students/{student_id}", tags=["Students"])
async def delete_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(User).filter(User.id == student_id, User.is_teacher == False).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    if student.avatar:
        filepath = os.path.join(AVATAR_DIR, student.avatar)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError as e:
                print(f"Ошибка при удалении файла {filepath}: {e}")
    all_projects = db.query(Project).all()
    for project in all_projects:
        if project.participants:
            project.participants = [p for p in project.participants if p.get("user_id") != student_id]
    db.delete(student)
    db.commit()
    return {"message": f"Student {student_id} deleted successfully"}

# ==================== УЧИТЕЛЯ ====================
@app.post("/auth/check-teacher-email", tags=["Auth"])
async def check_teacher_email(request: dict):
    email = request.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    if is_email_accepted(email):
        return {"accepted": True, "message": "Email разрешен для регистрации учителя"}
    else:
        raise HTTPException(status_code=403, detail="Этот email не разрешен для регистрации учителя. Используйте email из списка разрешенных.")

@app.post("/teachers/", response_model=TeacherResponse, tags=["Teachers"])
async def create_teacher(teacher: TeacherCreate, db: Session = Depends(get_db)):
    if not is_email_accepted(teacher.email):
        raise HTTPException(status_code=403, detail="Этот email не разрешен для регистрации учителя. Используйте email из списка разрешенных.")
    existing_nickname = db.query(User).filter(User.nickname == teacher.nickname.strip()).first()
    if existing_nickname:
        raise HTTPException(status_code=400, detail="Пользователь с таким никнеймом уже существует")
    existing_email = db.query(User).filter(User.email == teacher.email.strip()).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")
    hashed_password = get_password_hash(teacher.password.strip())
    teacher_info_dict = teacher.teacher_info.model_dump() if teacher.teacher_info else {}
    db_user = User(
        nickname=teacher.nickname.strip(),
        fullname=teacher.fullname,
        class_=None,
        speciality=teacher.speciality,
        email=teacher.email.strip(),
        password=hashed_password,
        avatar=None,
        is_active=True,
        is_verified=False,
        is_teacher=True,
        teacher_info=teacher_info_dict
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    code = generate_verification_code()
    redis_client.setex(f"verify:{teacher.email}", 600, code)
    await send_verification_email(teacher.email, code)
    return db_user

@app.post("/teachers/verify-and-create", response_model=TeacherResponse, tags=["Teachers"])
async def verify_and_create_teacher(request: dict, db: Session = Depends(get_db)):
    email = request.get("email")
    code = request.get("code")
    teacher_data = request.get("teacher_data")
    if not email or not code or not teacher_data:
        raise HTTPException(status_code=400, detail="Email, code and teacher data required")
    stored_code = redis_client.get(f"verify:{email}")
    if not stored_code or stored_code != code:
        raise HTTPException(status_code=400, detail="Invalid or expired verification code")
    redis_client.delete(f"verify:{email}")
    if not is_email_accepted(email):
        raise HTTPException(status_code=403, detail="Этот email не разрешен для регистрации учителя")
    existing_user = db.query(User).filter(
        (User.nickname == teacher_data.get('nickname')) |
        (User.email == email)
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Nickname or email already registered")
    hashed_password = get_password_hash(teacher_data.get('password'))
    db_user = User(
        nickname=teacher_data.get('nickname').strip(),
        fullname=teacher_data.get('fullname'),
        class_=None,
        speciality=teacher_data.get('speciality'),
        email=email,
        password=hashed_password,
        avatar=None,
        is_verified=True,
        is_active=True,
        is_teacher=True,
        teacher_info=teacher_data.get('teacher_info', {})
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/teachers/", response_model=List[TeacherResponse], tags=["Teachers"])
async def get_teachers(q: Optional[str] = Query(None), db: Session = Depends(get_db)):
    query = db.query(User).filter(User.is_teacher == True)
    if q:
        text_condition = or_(
            User.nickname.ilike(f"%{q}%"),
            User.fullname.ilike(f"%{q}%"),
            User.email.ilike(f"%{q}%"),
            User.speciality.ilike(f"%{q}%")
        )
        query = query.filter(text_condition)
    return query.all()

@app.get("/teachers/{teacher_id}", response_model=TeacherResponse, tags=["Teachers"])
async def get_teacher(teacher_id: int, db: Session = Depends(get_db)):
    teacher = db.query(User).filter(User.id == teacher_id, User.is_teacher == True).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    return teacher

@app.put("/teachers/{teacher_id}", response_model=TeacherResponse, tags=["Teachers"])
async def update_teacher(teacher_id: int, teacher_update: TeacherUpdate, db: Session = Depends(get_db)):
    teacher = db.query(User).filter(User.id == teacher_id, User.is_teacher == True).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    if teacher_update.fullname is not None:
        teacher.fullname = teacher_update.fullname
    if teacher_update.email is not None:
        existing = db.query(User).filter(User.email == teacher_update.email, User.id != teacher_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
        teacher.email = teacher_update.email
    if teacher_update.speciality is not None:
        teacher.speciality = teacher_update.speciality
    if teacher_update.teacher_info is not None:
        teacher.teacher_info = teacher_update.teacher_info.model_dump()
    db.commit()
    db.refresh(teacher)
    return teacher

@app.delete("/teachers/{teacher_id}", tags=["Teachers"])
async def delete_teacher(teacher_id: int, db: Session = Depends(get_db)):
    teacher = db.query(User).filter(User.id == teacher_id, User.is_teacher == True).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    if teacher.avatar:
        filepath = os.path.join(AVATAR_DIR, teacher.avatar)
        if os.path.exists(filepath):
            os.remove(filepath)
    all_projects = db.query(Project).all()
    for project in all_projects:
        if project.participants:
            project.participants = [p for p in project.participants if p.get("user_id") != teacher_id]
    db.delete(teacher)
    db.commit()
    return {"message": f"Teacher {teacher_id} deleted successfully"}

# ==================== ОБЩИЕ ПОЛЬЗОВАТЕЛИ ====================
@app.get("/users/me", response_model=UserResponse, tags=["Common"])
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

@app.get("/users/{user_id}", response_model=UserResponse, tags=["Common"])
async def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/users/", response_model=List[UserResponse], tags=["Common"])
async def search_all_users(
    q: Optional[str] = Query(None, description="Поисковый запрос"),
    user_type: Optional[str] = Query(None, description="Фильтр по типу: student или teacher"),
    db: Session = Depends(get_db)
):
    query = db.query(User)
    if user_type == "student":
        query = query.filter(User.is_teacher == False)
    elif user_type == "teacher":
        query = query.filter(User.is_teacher == True)
    if q:
        try:
            user_id = int(q)
            id_filter = (User.id == user_id)
        except ValueError:
            id_filter = None
        text_filters = [
            User.nickname.ilike(f"%{q}%"),
            User.fullname.ilike(f"%{q}%"),
            User.email.ilike(f"%{q}%")
        ]
        if id_filter is not None:
            query = query.filter(or_(id_filter, *text_filters))
        else:
            query = query.filter(or_(*text_filters))
    return query.all()

@app.post("/users/{user_id}/avatar", response_model=UserResponse, tags=["Common"])
async def upload_avatar(
    user_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Can only update your own avatar")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 5 MB)")
    try:
        img = Image.open(io.BytesIO(contents))
        width, height = img.get_size()
        crop_size = min(width, height)
        left = (width - crop_size) // 2
        top = (height - crop_size) // 2
        right = left + crop_size
        bottom = top + crop_size
        img = img.crop((left, top, right, bottom))
        img = img.resize((256, 256))
        unique_id = uuid.uuid4().hex[:8]
        filename = f"user_{user_id}_{unique_id}.webp"
        filepath = os.path.join("avatars", filename)
        img.save_as_webp(filepath)
        if user.avatar:
            old_path = os.path.join("avatars", user.avatar)
            if os.path.exists(old_path):
                os.remove(old_path)
        user.avatar = filename
        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        if 'filepath' in locals() and os.path.exists(filepath):
            os.remove(filepath)
        raise HTTPException(status_code=500, detail=f"Image processing failed: {str(e)}")

# ==================== ПРОЕКТЫ ====================
@app.get("/projects/old", response_model=List[ProjectResponse], tags=["Projects"])
async def get_old_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Project).filter(Project.is_old == True)
    if not (current_user.is_admin or is_curator(current_user)):
        query = query.filter(Project.is_hidden == False)
        all_projects = query.all()
        filtered = []
        for p in all_projects:
            if current_user.id not in (p.hidden_by_users or []):
                filtered.append(p)
        return filtered
    return query.all()

@app.put("/projects/{project_id}/mark-old", response_model=ProjectResponse, tags=["Projects"])
async def mark_project_old(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not (current_user.is_admin or is_curator(current_user)):
        raise HTTPException(403, "Only admin or curator can mark projects as old")
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    project.is_old = True
    db.commit()
    db.refresh(project)
    return project

@app.put("/projects/{project_id}/unmark-old", response_model=ProjectResponse, tags=["Projects"])
async def unmark_project_old(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not (current_user.is_admin or is_curator(current_user)):
        raise HTTPException(403, "Only admin or curator can unmark projects as old")
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    project.is_old = False
    db.commit()
    db.refresh(project)
    return project

@app.post("/projects/{project_id}/join-requests", response_model=ProjectResponse, tags=["Projects"])
async def create_join_request(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if any(p.get("user_id") == current_user.id for p in (project.participants or [])):
        raise HTTPException(status_code=400, detail="You are already a participant")
    if current_user.is_teacher:
        raise HTTPException(status_code=403, detail="Only students can request to join as executor")
    if project.join_requests:
        existing = next((r for r in project.join_requests if r.get("user_id") == current_user.id and r.get("status") == "pending"), None)
        if existing:
            raise HTTPException(status_code=400, detail="You already have a pending request")
    new_request = {
        "id": str(uuid.uuid4()),
        "user_id": current_user.id,
        "created_at": datetime.utcnow().isoformat(),
        "status": "pending"
    }
    if project.join_requests is None:
        project.join_requests = []
    project.join_requests.append(new_request)
    flag_modified(project, "join_requests")
    db.commit()
    db.refresh(project)
    return project

@app.patch("/projects/{project_id}/hide", response_model=ProjectResponse, tags=["Projects"])
async def toggle_hide_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.hidden_by_users is None:
        project.hidden_by_users = []
    if current_user.is_admin or is_curator(current_user):
        project.is_hidden = not project.is_hidden
        if project.is_hidden:
            project.hidden_by = current_user.id
        else:
            project.hidden_by = None
    else:
        participant = next((p for p in project.participants if p.get("user_id") == current_user.id), None)
        if not participant or participant.get("role") not in [ProjectRole.CUSTOMER.value, ProjectRole.EXECUTOR.value]:
            raise HTTPException(status_code=403, detail="Only customer, executor, curator or admin can hide/show projects")
        project.is_hidden = not project.is_hidden
        if project.is_hidden:
            project.hidden_by = current_user.id
        else:
            project.hidden_by = None
    db.commit()
    db.refresh(project)
    return project

@app.put("/projects/{project_id}/join-requests/{request_id}/accept", response_model=ProjectResponse, tags=["Projects"])
async def accept_join_request(
    project_id: int,
    request_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not (current_user.is_admin or is_curator(current_user)):
        role = get_participant_role(project, current_user.id)
        if role not in [ProjectRole.CUSTOMER.value, ProjectRole.CURATOR.value]:
            raise HTTPException(status_code=403, detail="Only customer, curator or admin can accept join requests")
    request = None
    for r in (project.join_requests or []):
        if r.get("id") == request_id:
            request = r
            break
    if not request:
        raise HTTPException(status_code=404, detail="Join request not found")
    if request.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Request already processed")
    request["status"] = "accepted"
    new_participant = {
        "user_id": request["user_id"],
        "role": ProjectRole.EXECUTOR.value,
        "joined_at": datetime.utcnow().isoformat()
    }
    if project.participants is None:
        project.participants = []
    project.participants.append(new_participant)
    flag_modified(project, "join_requests")
    flag_modified(project, "participants")
    db.commit()
    db.refresh(project)
    return project

@app.post("/projects/{project_id}/comments/{comment_id}/restore", response_model=ProjectResponse, tags=["Projects"])
async def restore_comment(
    project_id: int,
    comment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not (current_user.is_admin or is_curator(current_user)):
        raise HTTPException(status_code=403, detail="Only admin or curator can restore comments")
    comment = next((c for c in (project.comments or []) if c.get("id") == comment_id), None)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if not comment.get("hidden"):
        raise HTTPException(status_code=400, detail="Comment is not hidden")
    comment["hidden"] = False
    flag_modified(project, "comments")
    db.commit()
    db.refresh(project)
    return project

@app.post("/projects/{project_id}/tasks/{task_index}/comments/{comment_id}/restore", response_model=ProjectResponse, tags=["Projects"])
async def restore_task_comment(
    project_id: int,
    task_index: int,
    comment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not (current_user.is_admin or is_curator(current_user)):
        raise HTTPException(status_code=403, detail="Only admin or curator can restore comments")
    if not project.tasks or task_index < 0 or task_index >= len(project.tasks):
        raise HTTPException(status_code=404, detail="Task not found")
    task = project.tasks[task_index]
    comment = next((c for c in (task.get("comments") or []) if c.get("id") == comment_id), None)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if not comment.get("hidden"):
        raise HTTPException(status_code=400, detail="Comment is not hidden")
    comment["hidden"] = False
    flag_modified(project, "tasks")
    db.commit()
    db.refresh(project)
    return project

@app.put("/projects/{project_id}/join-requests/{request_id}/reject", response_model=ProjectResponse, tags=["Projects"])
async def reject_join_request(
    project_id: int,
    request_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not (current_user.is_admin or is_curator(current_user)):
        role = get_participant_role(project, current_user.id)
        if role not in [ProjectRole.CUSTOMER.value, ProjectRole.CURATOR.value]:
            raise HTTPException(status_code=403, detail="Only customer, curator or admin can reject join requests")
    request = None
    for r in (project.join_requests or []):
        if r.get("id") == request_id:
            request = r
            break
    if not request:
        raise HTTPException(status_code=404, detail="Join request not found")
    if request.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Request already processed")
    request["status"] = "rejected"
    flag_modified(project, "join_requests")
    db.commit()
    db.refresh(project)
    return project

@app.post("/projects/", response_model=ProjectResponse, tags=["Projects"])
async def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    creator_in_participants = any(p.user_id == current_user.id for p in project.participants)
    if not creator_in_participants:
        default_role = ProjectRole.EXECUTOR
        if current_user.is_teacher and current_user.teacher_info:
            roles = current_user.teacher_info.get("roles", [])
            if ProjectRole.CUSTOMER.value in roles:
                default_role = ProjectRole.CUSTOMER
            elif ProjectRole.SUPERVISOR.value in roles:
                default_role = ProjectRole.SUPERVISOR
            elif ProjectRole.EXPERT.value in roles:
                default_role = ProjectRole.EXPERT
            if current_user.teacher_info.get("curator"):
                default_role = ProjectRole.CURATOR
        project.participants.append(
            Participant(user_id=current_user.id, role=default_role, joined_at=datetime.utcnow())
        )
    user_ids = [p.user_id for p in project.participants]
    users = db.query(User).filter(User.id.in_(user_ids)).all()
    if len(users) != len(user_ids):
        raise HTTPException(status_code=404, detail="Один или несколько участников не найдены")
    if project.tasks:
        titles = [task.get('title', '').strip().lower() for task in project.tasks if task.get('title')]
        if len(titles) != len(set(titles)):
            raise HTTPException(status_code=400, detail="Task titles must be unique within a project")
    db_project = Project(
        title=project.title,
        body=project.body,
        underbody=project.underbody,
        participants=[p.model_dump(mode='json') for p in project.participants],
        tasks=project.tasks,
        links=project.links,
        comments=[c.model_dump(mode='json') for c in project.comments] if project.comments else [],
        is_hidden=False,
        hidden_by=None,
        hidden_by_users=[],
        is_old=False,
        ignore_file_limits=False
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@app.get("/projects/", response_model=List[ProjectResponse], tags=["Projects"])
async def get_projects(
    participant_id: Optional[int] = Query(None, description="ID участника для фильтрации проектов"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if participant_id is not None:
        all_projects = db.query(Project).all()
        projects = [
            p for p in all_projects
            if any(part.get("user_id") == participant_id for part in (p.participants or []))
        ]
        if not (current_user.is_admin or is_curator(current_user)):
            filtered_projects = []
            for p in projects:
                if not p.is_hidden:
                    hidden_by_users = p.hidden_by_users if p.hidden_by_users else []
                    if current_user.id not in hidden_by_users:
                        filtered_projects.append(p)
            return filtered_projects
        return projects
    else:
        query = db.query(Project)
        if not (current_user.is_admin or is_curator(current_user)):
            all_projects = query.filter(Project.is_hidden == False).all()
            filtered_projects = []
            for p in all_projects:
                hidden_by_users = p.hidden_by_users if p.hidden_by_users else []
                if current_user.id not in hidden_by_users:
                    filtered_projects.append(p)
            return filtered_projects
        return query.all()

@app.get("/projects/{project_id}", response_model=ProjectResponse, tags=["Projects"])
async def get_project_by_id(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not (current_user.is_admin or is_curator(current_user)):
        if project.is_hidden or current_user.id in (project.hidden_by_users or []):
            raise HTTPException(status_code=403, detail="Project is hidden")
    return project

@app.put("/projects/{project_id}", response_model=ProjectResponse, tags=["Projects"])
async def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.is_old and not (current_user.is_admin or is_curator(current_user)):
        raise HTTPException(status_code=403, detail="Старый проект нельзя редактировать. Только администратор может изменять его.")
    if not (current_user.is_admin or is_curator(current_user)):
        participant = next((p for p in project.participants if p.get("user_id") == current_user.id), None)
        if not participant or participant.get("role") not in [ProjectRole.CUSTOMER.value, ProjectRole.EXECUTOR.value]:
            raise HTTPException(status_code=403, detail="Only customer, executor, curator or admin can update the project")

    if project_update.title is not None:
        project.title = project_update.title
    if project_update.body is not None:
        project.body = project_update.body
    if project_update.underbody is not None:
        project.underbody = project_update.underbody

    if project_update.tasks is not None:
        old_tasks = project.tasks or []
        new_tasks = project_update.tasks

        for i, new_task in enumerate(new_tasks):
            old_task = old_tasks[i] if i < len(old_tasks) else None
            # Проверка обязательных файлов при завершении задачи
            if old_task and old_task.get("status") != "выполнена" and new_task.get("status") == "выполнена":
                required_files = new_task.get("required_files", [])
                if required_files:
                    for req in required_files:
                        req_id = req.get("id")
                        if not req_id:
                            continue
                        attached = db.query(ProjectFile).filter(
                            ProjectFile.project_id == project_id,
                            ProjectFile.task_id == i,
                            ProjectFile.required_file_id == req_id,
                            ProjectFile.is_deleted == False
                        ).first()
                        if not attached:
                            raise HTTPException(
                                401,
                                f"Для завершения задачи '{new_task.get('title')}' необходимо прикрепить файл: {req.get('name')}"
                            )
            # Сохраняем старые вложения, если в новом объекте задачи их нет
            if "attachments" not in new_task and old_task and "attachments" in old_task:
                new_task["attachments"] = old_task["attachments"]

        project.tasks = new_tasks
        flag_modified(project, "tasks")

    if project_update.links is not None:
        project.links = project_update.links
        flag_modified(project, "links")

    if project_update.comments is not None:
        project.comments = [c.model_dump(mode='json') for c in project_update.comments]
        flag_modified(project, "comments")

    if project_update.participants is not None:
        new_ids = [p.user_id for p in project_update.participants]
        users = db.query(User).filter(User.id.in_(new_ids)).all()
        if len(users) != len(new_ids):
            raise HTTPException(404, "One or more users not found")
        project.participants = [p.model_dump(mode='json') for p in project_update.participants]
        flag_modified(project, "participants")

    db.commit()
    db.refresh(project)
    return project

@app.delete("/files/{file_id}", tags=["Projects"])
async def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    file_record = db.query(ProjectFile).filter(ProjectFile.id == file_id).first()
    if not file_record:
        raise HTTPException(404, "File not found")
    project = db.query(Project).filter(Project.id == file_record.project_id).first()
    if not (current_user.id == file_record.uploaded_by or current_user.is_admin or is_curator(current_user) or is_project_participant(project, current_user.id)):
        raise HTTPException(403, "Not enough permissions")
    if file_record.task_id is not None:
        task = project.tasks[file_record.task_id]
        if "attachments" in task:
            task["attachments"] = [att for att in task["attachments"] if att.get("file_id") != file_id]
            flag_modified(project, "tasks")
    file_path = os.path.join("uploads", file_record.filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    db.delete(file_record)
    db.commit()
    return {"message": "File deleted"}

@app.get("/projects/{project_id}/files/required/{required_file_id}", response_model=List[ProjectFileResponse], tags=["Projects"])
async def get_files_by_required_id(
    project_id: int,
    required_file_id: str,
    task_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    if not (current_user.is_admin or is_curator(current_user) or is_project_participant(project, current_user.id)):
        raise HTTPException(403, "Not enough permissions")
    query = db.query(ProjectFile).filter(
        ProjectFile.project_id == project_id,
        ProjectFile.required_file_id == required_file_id,
        ProjectFile.is_deleted == False
    )
    if task_id is not None:
        query = query.filter(ProjectFile.task_id == task_id)
    files = query.all()
    return files

@app.post("/projects/{project_id}/comments", response_model=ProjectResponse, tags=["Projects"])
async def add_comment(
    project_id: int,
    comment: Comment,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not (current_user.is_admin or is_curator(current_user) or any(p.get("user_id") == current_user.id for p in (project.participants or []))):
        raise HTTPException(status_code=403, detail="Only project participants, curator or admin can comment")
    if project.comments is None:
        project.comments = []
    comment.authorId = current_user.id
    comment.authorRole = get_author_role(current_user, project)
    project.comments.append(comment.model_dump(mode='json'))
    flag_modified(project, "comments")
    try:
        db.commit()
        db.refresh(project)
        return project
    except Exception as e:
        print("Ошибка при сохранении комментария:", e)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/search", response_model=List[ProjectResponse], tags=["Projects"])
async def search_projects(q: Optional[str] = Query(None), db: Session = Depends(get_db)):
    if not q:
        return []
    return db.query(Project).filter(Project.title.ilike(f"%{q}%")).all()

@app.delete("/projects/{project_id}", tags=["Projects"])
async def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.hidden_by_users is None:
        project.hidden_by_users = []
    if current_user.is_admin or is_curator(current_user):
        db.delete(project)
        db.commit()
        return {"message": f"Project {project_id} permanently deleted successfully"}
    participant = next((p for p in project.participants if p.get("user_id") == current_user.id), None)
    if not participant or participant.get("role") not in [ProjectRole.CUSTOMER.value, ProjectRole.EXECUTOR.value]:
        raise HTTPException(status_code=403, detail="Only customer, executor, curator or admin can delete/hide the project")
    if current_user.id not in project.hidden_by_users:
        project.hidden_by_users.append(current_user.id)
    if not project.is_hidden:
        project.is_hidden = True
        project.hidden_by = current_user.id
    flag_modified(project, "hidden_by_users")
    db.commit()
    db.refresh(project)
    return {"message": f"Project {project_id} hidden successfully"}

@app.post("/projects/{project_id}/tasks/{task_index}/comments", response_model=ProjectResponse, tags=["Projects"])
async def add_task_comment(
    project_id: int,
    task_index: int,
    comment: Comment,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not (current_user.is_admin or is_curator(current_user) or any(p.get("user_id") == current_user.id for p in (project.participants or []))):
        raise HTTPException(status_code=403, detail="Only project participants, curator or admin can comment")
    if not project.tasks or task_index < 0 or task_index >= len(project.tasks):
        raise HTTPException(status_code=404, detail="Task not found")
    task = project.tasks[task_index]
    if task.get("comments") is None:
        task["comments"] = []
    comment.authorId = current_user.id
    comment.authorRole = get_author_role(current_user, project)
    task["comments"].append(comment.model_dump(mode='json'))
    flag_modified(project, "tasks")
    try:
        db.commit()
        db.refresh(project)
        return project
    except Exception as e:
        print("Ошибка при сохранении комментария к задаче:", e)
        raise HTTPException(status_code=500, detail="Internal server error")

# ==================== ПРЕДЛОЖЕНИЯ ====================
@app.post("/projects/{project_id}/suggestions", response_model=ProjectResponse, tags=["Projects"])
async def create_suggestion(
    project_id: int,
    suggestion_data: SuggestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not (current_user.is_admin or is_curator(current_user)):
        role = get_participant_role(project, current_user.id)
        if not role or role not in [ProjectRole.EXPERT.value, ProjectRole.SUPERVISOR.value, ProjectRole.EXECUTOR.value]:
            raise HTTPException(status_code=403, detail="Only expert, supervisor, executor, curator or admin can create suggestions")
    if suggestion_data.target_type not in ["project", "task", "link"]:
        raise HTTPException(status_code=400, detail="target_type must be 'project', 'task', or 'link'")
    new_suggestion = {
        "id": str(uuid.uuid4()),
        "author_id": current_user.id,
        "target_type": suggestion_data.target_type,
        "target_id": suggestion_data.target_id,
        "changes": suggestion_data.changes,
        "status": SuggestionStatus.PENDING.value,
        "created_at": datetime.utcnow().isoformat(),
        "comments": []
    }
    if project.suggestions is None:
        project.suggestions = []
    project.suggestions.append(new_suggestion)
    flag_modified(project, "suggestions")
    db.commit()
    db.refresh(project)
    return project

@app.put("/projects/{project_id}/suggestions/{suggestion_id}/accept", response_model=ProjectResponse, tags=["Projects"])
async def accept_suggestion(
    project_id: int,
    suggestion_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    suggestion = None
    for s in (project.suggestions or []):
        if s.get("id") == suggestion_id:
            suggestion = s
            break
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    if not (current_user.is_admin or is_curator(current_user)):
        role = get_participant_role(project, current_user.id)
        if not (suggestion.get("author_id") == current_user.id or role in [ProjectRole.CUSTOMER.value, ProjectRole.EXECUTOR.value]):
            raise HTTPException(status_code=403, detail="Only suggestion author, customer, executor, curator or admin can accept it")
    suggestion["status"] = SuggestionStatus.ACCEPTED.value
    flag_modified(project, "suggestions")
    if (role == ProjectRole.CUSTOMER.value or current_user.is_admin or is_curator(current_user)) and suggestion["target_type"] == "project":
        for key, value in suggestion["changes"].items():
            if hasattr(project, key):
                setattr(project, key, value)
    db.commit()
    db.refresh(project)
    return project

@app.put("/projects/{project_id}/suggestions/{suggestion_id}/reject", response_model=ProjectResponse, tags=["Projects"])
async def reject_suggestion(
    project_id: int,
    suggestion_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    suggestion = None
    for s in (project.suggestions or []):
        if s.get("id") == suggestion_id:
            suggestion = s
            break
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    if not (current_user.is_admin or is_curator(current_user)):
        role = get_participant_role(project, current_user.id)
        if not (suggestion.get("author_id") == current_user.id or role in [ProjectRole.CUSTOMER.value, ProjectRole.EXECUTOR.value]):
            raise HTTPException(status_code=403, detail="Only suggestion author, customer, executor, curator or admin can reject it")
    suggestion["status"] = SuggestionStatus.REJECTED.value
    flag_modified(project, "suggestions")
    db.commit()
    db.refresh(project)
    return project

# ==================== СКРЫТИЕ КОММЕНТАРИЕВ ====================
@app.post("/projects/{project_id}/comments/{comment_id}/hide", response_model=ProjectResponse, tags=["Projects"])
async def hide_comment(
    project_id: int,
    comment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not (current_user.is_admin or is_curator(current_user)):
        role = get_participant_role(project, current_user.id)
        if role != ProjectRole.SUPERVISOR.value:
            raise HTTPException(status_code=403, detail="Only supervisor, curator or admin can hide comments")
    comment = next((c for c in (project.comments or []) if c.get("id") == comment_id), None)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    comment["hidden"] = True
    flag_modified(project, "comments")
    db.commit()
    db.refresh(project)
    return project

# ==================== ПРИГЛАШЕНИЯ (по имейл) ====================
@app.post("/projects/{project_id}/invite", response_model=Dict[str, str], tags=["Projects"])
async def create_invitation(
    project_id: int,
    invite: InvitationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not (current_user.is_admin or is_curator(current_user)):
        role = get_participant_role(project, current_user.id)
        if role not in [ProjectRole.CUSTOMER.value, ProjectRole.SUPERVISOR.value]:
            raise HTTPException(status_code=403, detail="Only customer, supervisor, curator or admin can invite")
    token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(days=7)
    invite_data = {
        "project_id": project_id,
        "project_title": project.title,
        "role": invite.role.value,
        "invited_by": current_user.id,
        "email": invite.email,
        "expires_at": expires_at.isoformat()
    }
    redis_client.setex(f"invite:{token}", 7 * 24 * 60 * 60, json.dumps(invite_data))
    return {"token": token, "message": "Invitation created, email sending not implemented"}

@app.get("/invite/{token}", response_model=InvitationInfo, tags=["Invitations"])
async def get_invitation_info(token: str):
    data_str = redis_client.get(f"invite:{token}")
    if not data_str:
        raise HTTPException(status_code=404, detail="Invitation not found or expired")
    data = json.loads(data_str)
    return InvitationInfo(
        token=token,
        project_id=data["project_id"],
        project_title=data["project_title"],
        role=data["role"],
        invited_by=data["invited_by"],
        expires_at=datetime.fromisoformat(data["expires_at"])
    )

@app.post("/invite/{token}/accept", response_model=ProjectResponse, tags=["Invitations"])
async def accept_invitation(
    token: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    data_str = redis_client.get(f"invite:{token}")
    if not data_str:
        raise HTTPException(status_code=404, detail="Invitation not found or expired")
    data = json.loads(data_str)
    project = db.query(Project).filter(Project.id == data["project_id"]).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if any(p.get("user_id") == current_user.id for p in (project.participants or [])):
        raise HTTPException(status_code=400, detail="User already in project")
    new_participant = {
        "user_id": current_user.id,
        "role": data["role"],
        "joined_at": datetime.utcnow().isoformat(),
        "invited_by": data["invited_by"]
    }
    if project.participants is None:
        project.participants = []
    project.participants.append(new_participant)
    redis_client.delete(f"invite:{token}")
    db.commit()
    db.refresh(project)
    return project

# ==================== ФАЙЛЫ ПРОЕКТОВ ====================
@app.post("/projects/{project_id}/files", response_model=ProjectFileResponse, tags=["Projects"])
async def upload_project_file(
    project_id: int,
    file: UploadFile = File(...),
    task_id: Optional[int] = Form(None),
    required_file_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    if not (current_user.is_admin or is_curator(current_user) or is_project_participant(project, current_user.id)):
        raise HTTPException(403, "Not enough permissions")
    contents = await file.read()
    if not project.ignore_file_limits:
        limits = load_file_limits()
        if file.content_type not in limits:
            raise HTTPException(400, f"File type {file.content_type} not allowed")
        max_size = limits[file.content_type]
        if len(contents) > max_size:
            raise HTTPException(400, f"File too large (max {max_size // (1024*1024)} MB)")
    else:
        allowed = set(load_file_limits().keys())
        if file.content_type not in allowed:
            raise HTTPException(400, f"File type {file.content_type} not allowed")
    ext = os.path.splitext(file.filename)[1]
    unique_name = f"{uuid.uuid4().hex}{ext}"

    compressible_gzip = [
        "text/plain",
        "application/msword",
        "application/vnd.ms-powerpoint",
    ]
    image_compressible = [
        "image/png",
        "image/jpeg",
    ]

    compressed = False
    compressed_image = False
    final_content = contents
    final_filename = unique_name

    if file.content_type in compressible_gzip:
        compressed_content = gzip.compress(contents)
        if len(compressed_content) < len(contents):
            final_content = compressed_content
            final_filename = unique_name + ".gz"
            compressed = True

    elif file.content_type in image_compressible:
        try:
            img = PILImage.open(io.BytesIO(contents))
            max_dim = 1200
            w, h = img.size
            if w > max_dim or h > max_dim:
                ratio = min(max_dim / w, max_dim / h)
                new_size = (int(w * ratio), int(h * ratio))
                img = img.resize(new_size, PILImage.LANCZOS)
            output = io.BytesIO()
            img = img.convert("RGB")
            img.save(output, format="JPEG", quality=80)
            compressed_content = output.getvalue()
            if len(compressed_content) < len(contents):
                final_content = compressed_content
                final_filename = unique_name + ".jpg"
                compressed_image = True
        except Exception as e:
            print(f"Image compression failed, keeping original: {e}")

    file_path = os.path.join("uploads", final_filename)
    with open(file_path, "wb") as f:
        f.write(final_content)

    db_file = ProjectFile(
        project_id=project_id,
        task_id=task_id,
        filename=final_filename,
        required_file_id=required_file_id,
        original_filename=file.filename,
        file_size=len(contents),
        mime_type=file.content_type,
        uploaded_by=current_user.id,
        compressed=compressed or compressed_image
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)

    if task_id is not None:
        task = project.tasks[task_id]
        if "attachments" not in task:
            task["attachments"] = []
        attachment = {
            "id": str(uuid.uuid4()),
            "file_id": db_file.id,
            "required_file_id": required_file_id,
            "uploaded_at": datetime.utcnow().isoformat(),
            "original_filename": file.filename,
            "size": len(contents),
            "mime_type": file.content_type
        }
        task["attachments"].append(attachment)
        flag_modified(project, "tasks")
        db.commit()

    return db_file

@app.get("/projects/{project_id}/files", response_model=List[ProjectFileResponse], tags=["Projects"])
async def get_project_files(
    project_id: int,
    task_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")

    # Проверка прав: участники, админы, кураторы имеют доступ; для старых проектов доступ открыт всем
    if not (current_user.is_admin or is_curator(current_user) or is_project_participant(project, current_user.id)):
        if not project.is_old:
            raise HTTPException(403, "Not enough permissions")

    query = db.query(ProjectFile).filter(
        ProjectFile.project_id == project_id,
        ProjectFile.is_deleted == False
    )
    if task_id is not None:
        query = query.filter(ProjectFile.task_id == task_id)

    # Для старых проектов не-администраторы/не-кураторы видят только is_old_vision=True
    if project.is_old and not (current_user.is_admin or is_curator(current_user)):
        query = query.filter(ProjectFile.is_old_vision == True)

    files = query.all()
    return files

@app.delete("/admin/projects/{project_id}/files", tags=["Admin"])
async def admin_delete_all_project_files(
    project_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """Полностью удалить все файлы проекта (физические и записи в БД)."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")

    files = db.query(ProjectFile).filter(
        ProjectFile.project_id == project_id,
        ProjectFile.is_deleted == False
    ).all()

    # Удаляем физические файлы
    for f in files:
        file_path = os.path.join("uploads", f.filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError as e:
                print(f"Ошибка удаления файла {file_path}: {e}")
        db.delete(f)

    # Очищаем attachments в задачах проекта (чтобы не осталось висячих ссылок)
    if project.tasks:
        for task in project.tasks:
            if "attachments" in task:
                task["attachments"] = []
        flag_modified(project, "tasks")

    db.commit()
    return {"message": f"Все файлы проекта {project_id} удалены ({len(files)} шт.)"}

@app.patch("/files/{file_id}/set-requirement", tags=["Projects"])
async def set_file_requirement(
    file_id: int,
    data: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    file_record = db.query(ProjectFile).filter(ProjectFile.id == file_id).first()
    if not file_record:
        raise HTTPException(404, "File not found")
    project = db.query(Project).filter(Project.id == file_record.project_id).first()
    if not (current_user.is_admin or is_curator(current_user) or is_project_participant(project, current_user.id)):
        raise HTTPException(403, "Not enough permissions")

    new_required_id = data.get("required_file_id")
    file_record.required_file_id = new_required_id

    # если файл привязан к задаче, обновить attachment в JSON задачи
    if file_record.task_id is not None and project:
        task = project.tasks[file_record.task_id]
        for att in task.get("attachments", []):
            if att.get("file_id") == file_id:
                att["required_file_id"] = new_required_id
                break
        flag_modified(project, "tasks")

    db.commit()
    return {"message": "Requirement updated"}

@app.patch("/files/{file_id}/toggle-old-vision", tags=["Projects"])
async def toggle_file_old_vision(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    file_record = db.query(ProjectFile).filter(ProjectFile.id == file_id).first()
    if not file_record:
        raise HTTPException(404, "File not found")

    # Разрешаем только админу или куратору
    if not (current_user.is_admin or is_curator(current_user)):
        raise HTTPException(403, "Only admin or curator can change file visibility in old projects")

    file_record.is_old_vision = not file_record.is_old_vision
    db.commit()
    db.refresh(file_record)
    return file_record

@app.get("/files/{file_id}", tags=["Projects"])
async def download_file(
    file_id: int,
    request: Request,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user_from_query_or_header)
):
    file_record = db.query(ProjectFile).filter(ProjectFile.id == file_id).first()
    if not file_record:
        raise HTTPException(404, "File not found")
    project = db.query(Project).filter(Project.id == file_record.project_id).first()
    if not (current_user.is_admin or is_curator(current_user) or is_project_participant(project, current_user.id)):
        if not project.is_old:
            raise HTTPException(403, "Not enough permissions")
        # Запрещаем скачивать скрытые от старых проектов файлы
        if not file_record.is_old_vision:
            raise HTTPException(403, "File not available in old project")

    file_path = os.path.join("uploads", file_record.filename)
    if not os.path.exists(file_path):
        raise HTTPException(404, "File not found on disk")

    file_size = os.path.getsize(file_path)
    content_type = file_record.mime_type or "application/octet-stream"
    is_gzip = file_record.compressed and file_record.filename.endswith('.gz')

    range_header = request.headers.get("Range")
    if range_header and not is_gzip:
        try:
            range_value = range_header.strip().lower()
            if not range_value.startswith("bytes="):
                raise ValueError("Invalid range unit")
            range_value = range_value[6:]
            if range_value.startswith("-"):
                end = file_size - 1
                start = file_size - int(range_value[1:])
                if start < 0:
                    start = 0
            elif range_value.endswith("-"):
                start = int(range_value[:-1])
                end = file_size - 1
            else:
                parts = range_value.split('-')
                start = int(parts[0])
                end = int(parts[1]) if parts[1] else file_size - 1
        except (ValueError, IndexError):
            raise HTTPException(status_code=416, detail="Invalid Range header")

        if start >= file_size or end >= file_size or start > end:
            raise HTTPException(status_code=416, detail="Range not satisfiable")

        chunk_size = end - start + 1

        def iterfile():
            with open(file_path, "rb") as f:
                f.seek(start)
                remaining = chunk_size
                while remaining > 0:
                    data = f.read(min(4096, remaining))
                    if not data:
                        break
                    remaining -= len(data)
                    yield data

        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(chunk_size),
            "Content-Disposition": f"inline; filename=\"{file_record.original_filename}\"",
        }
        return StreamingResponse(iterfile(), status_code=206, media_type=content_type, headers=headers)

    headers = {"Content-Disposition": "inline"}
    if is_gzip:
        headers["Content-Encoding"] = "gzip"
    return FileResponse(file_path, filename=file_record.original_filename, media_type=content_type, headers=headers)

# ==================== АУТЕНТИФИКАЦИЯ И ВЕРИФИКАЦИЯ ====================
@app.post("/auth/request-verification-code", tags=["Auth"])
async def request_verification_code(request: dict, db: Session = Depends(get_db)):
    email = request.get("email")
    is_teacher = request.get("is_teacher", False)
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    if is_teacher:
        if not is_email_accepted(email):
            raise HTTPException(status_code=403, detail="Этот email не разрешен для регистрации учителя")
    else:
        if not is_student_email_accepted(email):
            raise HTTPException(status_code=403, detail="Этот email не разрешён для регистрации ученика. Используйте email с доменом lit1533.ru или из списка разрешённых.")
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    code = generate_verification_code()
    redis_client.setex(f"verify:{email}", 600, code)
    await send_verification_email(email, code)
    return {"message": "Verification code sent"}

@app.post("/auth/request-verification", tags=["Auth"])
async def request_verification(request: EmailVerificationCodeRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_verified:
        raise HTTPException(status_code=400, detail="Email already verified")
    code = generate_verification_code()
    redis_client.setex(f"verify:{request.email}", 600, code)
    await send_verification_email(request.email, code)
    return {"message": "Verification code sent"}

@app.post("/auth/verify-email", tags=["Auth"])
async def verify_email(request: dict, db: Session = Depends(get_db)):
    email = request.get("email")
    code = request.get("code")
    if not email or not code:
        raise HTTPException(status_code=400, detail="Email and code required")
    stored_code = redis_client.get(f"verify:{email}")
    if not stored_code or stored_code != code:
        raise HTTPException(status_code=400, detail="Invalid or expired code")
    redis_client.delete(f"verify:{email}")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_verified = True
    db.commit()
    db.refresh(user)
    return {"message": "Email successfully verified", "user": user}

@app.post("/auth/register-with-verification", response_model=UserResponse, tags=["Auth"])
async def register_with_verification(request: dict, db: Session = Depends(get_db)):
    email = request.get("email")
    code = request.get("code")
    user_data = request.get("user_data")
    is_teacher = request.get("is_teacher", False)
    if not email or not code or not user_data:
        raise HTTPException(status_code=400, detail="Email, code and user data required")
    stored_code = redis_client.get(f"verify:{email}")
    if not stored_code or stored_code != code:
        raise HTTPException(status_code=400, detail="Invalid or expired verification code")
    redis_client.delete(f"verify:{email}")
    if is_teacher:
        if not is_email_accepted(email):
            raise HTTPException(status_code=403, detail="Этот email не разрешен для регистрации учителя")
    else:
        if not is_student_email_accepted(email):
            raise HTTPException(status_code=403, detail="Этот email не разрешён для регистрации ученика")
    existing_user = db.query(User).filter(
        (User.nickname == user_data.get('nickname')) |
        (User.email == email)
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Nickname or email already registered")
    hashed_password = get_password_hash(user_data.get('password'))
    if is_teacher:
        teacher_info = user_data.get('teacher_info', {})
        db_user = User(
            nickname=user_data.get('nickname').strip(),
            fullname=user_data.get('fullname'),
            class_=None,
            speciality=user_data.get('speciality'),
            email=email,
            password=hashed_password,
            avatar=None,
            is_verified=True,
            is_active=True,
            is_teacher=True,
            teacher_info=teacher_info
        )
    else:
        db_user = User(
            nickname=user_data.get('nickname').strip(),
            fullname=user_data.get('fullname'),
            class_=user_data.get('class_', 0),
            speciality=user_data.get('speciality'),
            email=email,
            password=hashed_password,
            avatar=None,
            is_verified=True,
            is_active=True,
            is_teacher=False,
            teacher_info=None
        )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/auth/login", response_model=TokenResponse, tags=["Auth"])
async def auth_login(credentials: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        (User.nickname == credentials.nickname.strip()) |
        (User.email == credentials.nickname.strip())
    ).first()
    if not user:
        raise HTTPException(status_code=402, detail="Пользователь с таким логином не найден")
    if not verify_password(credentials.password.strip(), user.password):
        raise HTTPException(status_code=402, detail="Неверный пароль")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Пользователь забанен")
    access_token = create_access_token({"sub": str(user.id), "is_teacher": user.is_teacher})
    refresh_token = create_refresh_token({"sub": str(user.id), "is_teacher": user.is_teacher})
    redis_client.setex(f"refresh:{user.id}:{refresh_token}", REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60, "valid")
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)

@app.post("/auth/refresh", response_model=TokenResponse, tags=["Auth"])
async def refresh_token(request: Request, db: Session = Depends(get_db)):
    refresh_token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not refresh_token:
        raise HTTPException(status_code=402, detail="Refresh token required")
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
        if not redis_client.get(f"refresh:{user_id}:{refresh_token}"):
            raise HTTPException(status_code=402, detail="Invalid refresh token")
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise HTTPException(status_code=402, detail="User not found or inactive")
        new_access_token = create_access_token({"sub": str(user.id), "is_teacher": user.is_teacher})
        new_refresh_token = create_refresh_token({"sub": str(user.id), "is_teacher": user.is_teacher})
        redis_client.delete(f"refresh:{user_id}:{refresh_token}")
        redis_client.setex(f"refresh:{user_id}:{new_refresh_token}", REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60, "valid")
        return TokenResponse(access_token=new_access_token, refresh_token=new_refresh_token)
    except JWTError:
        raise HTTPException(status_code=402, detail="Invalid refresh token")

@app.post("/auth/logout", tags=["Auth"])
async def logout(request: Request, current_user: User = Depends(get_current_user)):
    refresh_token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if refresh_token:
        redis_client.delete(f"refresh:{current_user.id}:{refresh_token}")
    return {"message": "Logged out successfully"}

# ==================== УДАЛЕНИЕ КОММЕНТАРИЕВ (СКРЫТИЕ) ====================
@app.delete("/projects/{project_id}/comments/{comment_id}", response_model=ProjectResponse, tags=["Projects"])
async def delete_project_comment(
    project_id: int,
    comment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not (current_user.is_admin or is_curator(current_user) or any(p.get("user_id") == current_user.id for p in (project.participants or []))):
        raise HTTPException(status_code=403, detail="Only project participants, curator or admin can modify comments")
    comment = next((c for c in (project.comments or []) if c.get("id") == comment_id), None)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if not (current_user.is_admin or is_curator(current_user) or comment.get("authorId") == current_user.id):
        role = get_participant_role(project, current_user.id)
        if role != ProjectRole.CUSTOMER.value:
            raise HTTPException(status_code=403, detail="Only comment author, customer, curator or admin can delete")
    comment["hidden"] = True
    flag_modified(project, "comments")
    db.commit()
    db.refresh(project)
    return project

@app.delete("/projects/{project_id}/tasks/{task_index}/comments/{comment_id}", response_model=ProjectResponse, tags=["Projects"])
async def delete_task_comment(
    project_id: int,
    task_index: int,
    comment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not (current_user.is_admin or is_curator(current_user) or any(p.get("user_id") == current_user.id for p in (project.participants or []))):
        raise HTTPException(status_code=403, detail="Only project participants, curator or admin can modify comments")
    if not project.tasks or task_index < 0 or task_index >= len(project.tasks):
        raise HTTPException(status_code=404, detail="Task not found")
    task = project.tasks[task_index]
    if task.get("comments") is None:
        raise HTTPException(status_code=404, detail="Comments not found")
    comment = next((c for c in task["comments"] if c.get("id") == comment_id), None)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if not (current_user.is_admin or is_curator(current_user) or comment.get("authorId") == current_user.id):
        role = get_participant_role(project, current_user.id)
        if role != ProjectRole.CUSTOMER.value:
            raise HTTPException(status_code=403, detail="Only comment author, customer, curator or admin can delete")
    comment["hidden"] = True
    flag_modified(project, "tasks")
    db.commit()
    db.refresh(project)
    return project

# ==================== ОТМЕТКА ПРОЧИТАННЫХ КОММЕНТАРИЕВ ====================
@app.put("/projects/{project_id}/comments/{comment_id}/read", response_model=ProjectResponse, tags=["Projects"])
async def mark_project_comment_read(
    project_id: int,
    comment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not (current_user.is_admin or is_curator(current_user) or any(p.get("user_id") == current_user.id for p in (project.participants or []))):
        raise HTTPException(status_code=403, detail="Only project participants, curator or admin can modify comments")
    comment = next((c for c in (project.comments or []) if c.get("id") == comment_id), None)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    comment["isRead"] = True
    flag_modified(project, "comments")
    db.commit()
    db.refresh(project)
    return project

@app.put("/projects/{project_id}/tasks/{task_index}/comments/{comment_id}/read", response_model=ProjectResponse, tags=["Projects"])
async def mark_task_comment_read(
    project_id: int,
    task_index: int,
    comment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not (current_user.is_admin or is_curator(current_user) or any(p.get("user_id") == current_user.id for p in (project.participants or []))):
        raise HTTPException(status_code=403, detail="Only project participants, curator or admin can modify comments")
    if not project.tasks or task_index < 0 or task_index >= len(project.tasks):
        raise HTTPException(status_code=404, detail="Task not found")
    task = project.tasks[task_index]
    comment = next((c for c in (task.get("comments") or []) if c.get("id") == comment_id), None)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    comment["isRead"] = True
    flag_modified(project, "tasks")
    db.commit()
    db.refresh(project)
    return project

# ==================== УПРАВЛЕНИЕ РАЗРЕШЁННЫМИ EMAIL ====================
@app.get("/admin/accepted-emails/teachers", tags=["Admin"])
async def get_accepted_teacher_emails(
    admin: User = Depends(get_current_admin)
):
    try:
        with open(ACCEPTED_EMAILS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        return {"accepted_emails": [], "domains": []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка чтения файла: {str(e)}")

@app.put("/admin/accepted-emails/teachers", tags=["Admin"])
async def update_accepted_teacher_emails(
    data: dict,
    admin: User = Depends(get_current_admin)
):
    if "accepted_emails" not in data or "domains" not in data:
        raise HTTPException(status_code=400, detail="Неверная структура: требуется accepted_emails и domains")
    if not isinstance(data["accepted_emails"], list) or not isinstance(data["domains"], list):
        raise HTTPException(status_code=400, detail="accepted_emails и domains должны быть массивами")
    try:
        with open(ACCEPTED_EMAILS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return {"message": "Файл успешно обновлён"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка записи файла: {str(e)}")

@app.get("/admin/accepted-emails/students", tags=["Admin"])
async def get_accepted_student_emails(
    admin: User = Depends(get_current_admin)
):
    try:
        with open(ACCEPTED_STUDENT_EMAILS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        return {"accepted_emails": [], "domains": ["lit1533.ru"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка чтения файла: {str(e)}")

@app.put("/admin/accepted-emails/students", tags=["Admin"])
async def update_accepted_student_emails(
    data: dict,
    admin: User = Depends(get_current_admin)
):
    if "accepted_emails" not in data or "domains" not in data:
        raise HTTPException(status_code=400, detail="Неверная структура: требуется accepted_emails и domains")
    if not isinstance(data["accepted_emails"], list) or not isinstance(data["domains"], list):
        raise HTTPException(status_code=400, detail="accepted_emails и domains должны быть массивами")
    try:
        with open(ACCEPTED_STUDENT_EMAILS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return {"message": "Файл успешно обновлён"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка записи файла: {str(e)}")

# ==================== УПРАВЛЕНИЕ ШАБЛОНАМИ ЗАДАЧ ====================
@app.put("/admin/default-tasks/class/{class_key}/direction/{direction_key}", tags=["Admin"])
async def update_direction(
    class_key: str,
    direction_key: str,
    data: dict = Body(...),
    admin: User = Depends(get_current_admin)
):
    default_tasks = load_default_tasks()
    if class_key not in default_tasks:
        raise HTTPException(404, "Class not found")
    if "directions" not in default_tasks[class_key] or direction_key not in default_tasks[class_key]["directions"]:
        raise HTTPException(404, "Direction not found")
    new_label = data.get("new_label")
    new_key = data.get("new_key")
    if new_label:
        default_tasks[class_key]["directions"][direction_key]["label"] = new_label
    if new_key and new_key != direction_key:
        if new_key in default_tasks[class_key]["directions"]:
            raise HTTPException(400, "Direction key already exists")
        default_tasks[class_key]["directions"][new_key] = default_tasks[class_key]["directions"][direction_key]
        del default_tasks[class_key]["directions"][direction_key]
    save_default_tasks(default_tasks)
    return {"message": "Direction updated"}

@app.put("/admin/default-tasks", tags=["Admin"])
async def update_default_tasks_full(
    data: Dict[str, Any] = Body(...),
    admin: User = Depends(get_current_admin)
):
    save_default_tasks(data)
    return {"message": "Default tasks updated"}

@app.post("/admin/default-tasks/class", tags=["Admin"])
async def add_class(
    class_key: str = Body(...),
    label: str = Body(...),
    admin: User = Depends(get_current_admin)
):
    data = load_default_tasks()
    if class_key in data:
        raise HTTPException(400, "Class already exists")
    data[class_key] = {"label": label, "tasks": []}
    save_default_tasks(data)
    return {"message": "Class added"}

@app.delete("/admin/default-tasks/class/{class_key}", tags=["Admin"])
async def delete_class(
    class_key: str,
    admin: User = Depends(get_current_admin)
):
    data = load_default_tasks()
    if class_key not in data:
        raise HTTPException(404, "Class not found")
    del data[class_key]
    save_default_tasks(data)
    return {"message": "Class deleted"}

@app.post("/admin/default-tasks/class/{class_key}/direction", tags=["Admin"])
async def add_direction(
    class_key: str,
    direction_key: str = Body(...),
    label: str = Body(...),
    admin: User = Depends(get_current_admin)
):
    data = load_default_tasks()
    if class_key not in data:
        raise HTTPException(404, "Class not found")
    if "directions" not in data[class_key]:
        data[class_key]["directions"] = {}
    if direction_key in data[class_key]["directions"]:
        raise HTTPException(400, "Direction already exists")
    data[class_key]["directions"][direction_key] = {"label": label, "tasks": []}
    save_default_tasks(data)
    return {"message": "Direction added"}

@app.delete("/admin/default-tasks/class/{class_key}/direction/{direction_key}", tags=["Admin"])
async def delete_direction(
    class_key: str,
    direction_key: str,
    admin: User = Depends(get_current_admin)
):
    data = load_default_tasks()
    if class_key not in data or "directions" not in data[class_key]:
        raise HTTPException(404, "Class or directions not found")
    if direction_key not in data[class_key]["directions"]:
        raise HTTPException(404, "Direction not found")
    del data[class_key]["directions"][direction_key]
    save_default_tasks(data)
    return {"message": "Direction deleted"}

@app.put("/admin/default-tasks/class/{class_key}/tasks", tags=["Admin"])
async def update_class_tasks(
    class_key: str,
    tasks: List[TaskTemplate] = Body(...),
    admin: User = Depends(get_current_admin)
):
    data = load_default_tasks()
    if class_key not in data:
        raise HTTPException(404, "Class not found")
    data[class_key]["tasks"] = [t.dict() for t in tasks]
    save_default_tasks(data)
    return {"message": "Tasks updated"}

@app.put("/admin/default-tasks/class/{class_key}/direction/{direction_key}/tasks", tags=["Admin"])
async def update_direction_tasks(
    class_key: str,
    direction_key: str,
    tasks: List[TaskTemplate] = Body(...),
    admin: User = Depends(get_current_admin)
):
    data = load_default_tasks()
    if class_key not in data or "directions" not in data[class_key]:
        raise HTTPException(404, "Class or directions not found")
    if direction_key not in data[class_key]["directions"]:
        raise HTTPException(404, "Direction not found")
    data[class_key]["directions"][direction_key]["tasks"] = [t.dict() for t in tasks]
    save_default_tasks(data)
    return {"message": "Tasks updated"}

# ==================== ПРИГЛАШЕНИЯ (НОВАЯ ВЕРСИЯ) ====================
@app.post("/invitations", response_model=InvitationResponse, tags=["Invitations"])
async def create_invitation(
    invite: InvitationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == invite.project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    if not (current_user.is_admin or is_curator(current_user)):
        role = get_participant_role(project, current_user.id)
        if role not in [ProjectRole.CUSTOMER.value, ProjectRole.SUPERVISOR.value, ProjectRole.EXECUTOR.value]:
            raise HTTPException(403, "Only customer, supervisor, executor, curator or admin can invite")
    invited_user = db.query(User).filter(User.id == invite.invited_user_id).first()
    if not invited_user:
        raise HTTPException(404, "User not found")
    if any(p.get("user_id") == invite.invited_user_id for p in (project.participants or [])):
        raise HTTPException(400, "User is already a participant")
    existing = db.query(Invitation).filter(
        Invitation.project_id == invite.project_id,
        Invitation.invited_user_id == invite.invited_user_id,
        Invitation.role == invite.role.value,
        Invitation.status == "pending"
    ).first()
    if existing:
        raise HTTPException(400, "Invitation already pending for this user in this project")
    db_invite = Invitation(
        project_id=invite.project_id,
        invited_by=current_user.id,
        invited_user_id=invite.invited_user_id,
        role=invite.role.value,
        status="pending"
    )
    db.add(db_invite)
    db.commit()
    db.refresh(db_invite)
    db_invite.project_title = project.title
    db_invite.invited_by_nickname = current_user.nickname
    return db_invite

@app.get("/invitations", response_model=List[InvitationResponse], tags=["Invitations"])
async def get_my_invitations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    invites = db.query(Invitation).filter(
        Invitation.invited_user_id == current_user.id,
        Invitation.status == "pending"
    ).all()
    for inv in invites:
        proj = db.query(Project).filter(Project.id == inv.project_id).first()
        inv.project_title = proj.title if proj else "Unknown"
        inviter = db.query(User).filter(User.id == inv.invited_by).first()
        inv.invited_by_nickname = inviter.nickname if inviter else "Unknown"
    return invites

@app.get("/invitations/sent", response_model=List[InvitationResponse], tags=["Invitations"])
async def get_sent_invitations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    invites = db.query(Invitation).filter(
        Invitation.invited_by == current_user.id
    ).all()
    for inv in invites:
        proj = db.query(Project).filter(Project.id == inv.project_id).first()
        inv.project_title = proj.title if proj else "Unknown"
        inv.invited_by_nickname = current_user.nickname
    return invites

@app.put("/invitations/{invitation_id}/accept", response_model=ProjectResponse, tags=["Invitations"])
async def accept_invitation(
    invitation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    invite = db.query(Invitation).filter(Invitation.id == invitation_id).first()
    if not invite:
        raise HTTPException(404, "Invitation not found")
    if invite.invited_user_id != current_user.id:
        raise HTTPException(403, "Not your invitation")
    if invite.status != "pending":
        raise HTTPException(400, "Invitation already processed")
    project = db.query(Project).filter(Project.id == invite.project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    if project.participants is None:
        project.participants = []
    project.participants.append({
        "user_id": current_user.id,
        "role": invite.role,
        "joined_at": datetime.utcnow().isoformat(),
        "invited_by": invite.invited_by
    })
    flag_modified(project, "participants")
    invite.status = "accepted"
    db.commit()
    db.refresh(project)
    return project

@app.put("/invitations/{invitation_id}/reject", response_model=InvitationResponse, tags=["Invitations"])
async def reject_invitation(
    invitation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    invite = db.query(Invitation).filter(Invitation.id == invitation_id).first()
    if not invite:
        raise HTTPException(404, "Invitation not found")
    if invite.invited_user_id != current_user.id:
        raise HTTPException(403, "Not your invitation")
    if invite.status != "pending":
        raise HTTPException(400, "Invitation already processed")
    invite.status = "rejected"
    db.commit()
    db.refresh(invite)
    return invite

@app.delete("/invitations/{invitation_id}", tags=["Invitations"])
async def cancel_invitation(
    invitation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    invite = db.query(Invitation).filter(Invitation.id == invitation_id).first()
    if not invite:
        raise HTTPException(404, "Invitation not found")
    if invite.invited_by != current_user.id and not current_user.is_admin:
        raise HTTPException(403, "Only the inviter or admin can cancel")
    if invite.status != "pending":
        raise HTTPException(400, "Can only cancel pending invitations")
    db.delete(invite)
    db.commit()
    return {"message": "Invitation cancelled"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)