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
from oauth_routes import router as oauth_router
load_dotenv()
from sqlalchemy.orm.attributes import flag_modified
from models import Base, User, Project, ProjectFile, Invitation, ProjectCheckpoint, ProjectChange  # ← Добавлены новые модели
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
    RequiredFile, TaskTemplate,
    ApprovalStatus, ApprovalInfo, ApprovalAction, ApprovalRequest, ProjectApprovalList,
    # Новые схемы для версионирования ← Добавлены
    ProjectCheckpointResponse, ProjectChangeResponse,
    ProjectVersionDetail, ProjectVersionHistory, ProjectVersionStats,
    CreateCheckpointRequest, CreateCheckpointResponse,
    RestoreVersionResponse, DeleteVersionResponse
)

from willow import Image
from PIL import Image as PILImage
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig

from auth import (
    verify_password, get_password_hash, create_access_token, create_refresh_token,
    get_current_user, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS, oauth2_scheme
)

from fastapi.security import OAuth2PasswordRequestFormStrict
from email_utils import generate_verification_code, send_verification_email, send_password_reset_email
from core.memory_store import memory_store as redis_client

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

app = FastAPI(title="School Platform API", description="API для управления учениками, учителями и проектами")

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

ADMIN_INIT_PASSWORD = os.getenv("ADMIN_INIT_PASSWORD", "SuperMegaSilvaAdmin")
DEFAULT_TASKS_FILE = "default_tasks.json"
FILE_SIZE_LIMITS_FILE = "file_size_limits.json"

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
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
app.include_router(oauth_router)

# ==================== СИСТЕМА ОЧКОВ СЛОЖНОСТИ ====================

CHANGE_POINTS = {
    # 1 очко - мелкие изменения
    "comment_add": 1,
    "comment_delete": 1,
    "comment_restore": 1,
    "comment_mark_read": 1,
    "task_comment_add": 1,
    "task_comment_delete": 1,
    "task_comment_restore": 1,
    "link_update": 1,
    "link_delete": 1,
    "gantt_update": 1,
    "subtask_move": 1,
    "task_reorder": 1,
    "task_move": 1,
    
    # 3 очка - изменения уровня задач
    "task_update": 3,
    "task_status_change": 3,
    "tasks_bulk_update": 3,
    "file_upload": 3,
    "file_delete": 3,
    "file_requirement_set": 3,
    "file_old_vision_toggle": 3,
    "suggestion_create": 3,
    "suggestion_accept": 3,
    "suggestion_reject": 3,
    "join_request_create": 3,
    "join_request_accept": 3,
    "join_request_reject": 3,
    "invitation_create": 3,
    "invitation_accept": 3,
    "invitation_reject": 3,
    "invitation_cancel": 3,
    
    # 5 очков - изменения уровня проекта
    "project_title_update": 5,
    "project_body_update": 5,
    "project_underbody_update": 5,
    "project_full_update": 5,
    "participant_add": 5,
    "participant_remove": 5,
    "participant_role_change": 5,
    "required_roles_change": 5,
    "project_approval_request": 5,
    "project_approval_cancel": 5,
    "project_approval_decision": 5,
    "project_hide_toggle": 5,
    "project_mark_old": 5,
    "project_unmark_old": 5,
    "project_leave": 5,
    
    # 10 очков - критические изменения
    "project_create": 10,
    "project_delete": 10,
    "admin_delete_project": 10,
    "admin_delete_all_files": 10,
    "admin_update_project": 5,
    "admin_toggle_file_limits": 3,
}

POINTS_THRESHOLD = 50  # Порог для автоматического чекпоинта


# ==================== ФУНКЦИИ ДЛЯ РАБОТЫ СО СНИМКАМИ ====================

def create_project_snapshot(project: Project) -> dict:
    """Создаёт полный снимок текущего состояния проекта."""
    return {
        "title": project.title,
        "body": project.body,
        "underbody": project.underbody,
        "participants": project.participants,
        "tasks": project.tasks,
        "links": project.links,
        "comments": project.comments,
        "suggestions": project.suggestions,
        "join_requests": project.join_requests,
        "required_roles": project.required_roles,
        "is_hidden": project.is_hidden,
        "hidden_by": project.hidden_by,
        "hidden_by_users": project.hidden_by_users,
        "is_old": project.is_old,
        "ignore_file_limits": project.ignore_file_limits,
        # Поля одобрения
        "is_approved": getattr(project, 'is_approved', False),
        "approval_status": getattr(project, 'approval_status', 'draft'),
        "approval_requested_at": project.approval_requested_at.isoformat() if getattr(project, 'approval_requested_at', None) else None,
        "approval_requested_by": getattr(project, 'approval_requested_by', None),
        "approval_handled_at": project.approval_handled_at.isoformat() if getattr(project, 'approval_handled_at', None) else None,
        "approval_handled_by": getattr(project, 'approval_handled_by', None),
        "approval_comment": getattr(project, 'approval_comment', None),
    }


def compute_project_diff(old_snapshot: dict, new_snapshot: dict) -> dict:
    """Вычисляет разницу между двумя снимками проекта.
    Возвращает словарь только с изменившимися полями."""
    diff = {}
    for key in new_snapshot:
        if key not in old_snapshot or old_snapshot[key] != new_snapshot[key]:
            diff[key] = new_snapshot[key]
    return diff


def apply_diff(base_snapshot: dict, diff: dict) -> dict:
    """Применяет diff к базовому снимку.
    Возвращает новый снимок с применёнными изменениями."""
    result = base_snapshot.copy()
    for key, value in diff.items():
        result[key] = value
    return result


# ==================== ФУНКЦИИ ДЛЯ РАБОТЫ С ЧЕКПОИНТАМИ ====================

def get_current_checkpoint_version(db: Session, project_id: int) -> int:
    """Получает номер последнего чекпоинта проекта. 0 если нет."""
    last = db.query(ProjectCheckpoint).filter(
        ProjectCheckpoint.project_id == project_id
    ).order_by(ProjectCheckpoint.version.desc()).first()
    return last.version if last else 0


def get_current_change_version(db: Session, project_id: int, checkpoint_version: int) -> int:
    """Получает номер последнего изменения в чекпоинте. 0 если нет."""
    last = db.query(ProjectChange).filter(
        ProjectChange.project_id == project_id,
        ProjectChange.checkpoint_version == checkpoint_version
    ).order_by(ProjectChange.change_version.desc()).first()
    return last.change_version if last else 0


def get_total_points_since_last_checkpoint(db: Session, project_id: int) -> int:
    """Считает сумму очков всех изменений после последнего чекпоинта."""
    last_checkpoint = db.query(ProjectCheckpoint).filter(
        ProjectCheckpoint.project_id == project_id
    ).order_by(ProjectCheckpoint.version.desc()).first()
    
    if not last_checkpoint:
        return 0
    
    changes = db.query(ProjectChange).filter(
        ProjectChange.project_id == project_id,
        ProjectChange.checkpoint_version == last_checkpoint.version
    ).all()
    
    return sum(c.points for c in changes)


# ==================== ОСНОВНЫЕ ФУНКЦИИ ВЕРСИОНИРОВАНИЯ ====================

async def record_change(
    db: Session,
    project_id: int,
    change_type: str,
    points: int,
    diff: dict,
    user_id: int,
    description: str = ""
):
    """
    Записывает изменение в историю.
    Если нет чекпоинта - создаёт первый.
    Если накоплено >= POINTS_THRESHOLD очков - создаёт авто-чекпоинт.
    """
    # Получаем или создаём чекпоинт
    cp_version = get_current_checkpoint_version(db, project_id)
    if cp_version == 0:
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            cp_version = await create_checkpoint(db, project, user_id, "Initial checkpoint")
    
    # Определяем номер изменения
    ch_version = get_current_change_version(db, project_id, cp_version) + 1
    
    # Создаём запись об изменении
    change = ProjectChange(
        project_id=project_id,
        checkpoint_version=cp_version,
        change_version=ch_version,
        change_type=change_type,
        points=points,
        diff=diff,
        created_by=user_id,
        description=description
    )
    db.add(change)
    db.flush()  # Сохраняем без коммита
    
    # Проверяем, не пора ли создать авто-чекпоинт
    total_points = get_total_points_since_last_checkpoint(db, project_id)
    if total_points >= POINTS_THRESHOLD:
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            await create_checkpoint(
                db, project, user_id,
                f"Auto-checkpoint: {total_points} points accumulated",
                total_points
            )
    
    return change


async def create_checkpoint(
    db: Session,
    project: Project,
    user_id: int,
    message: str = "",
    total_points: int = 0
) -> int:
    """
    Создаёт новый чекпоинт с полным снимком проекта.
    Возвращает номер новой версии.
    """
    version = get_current_checkpoint_version(db, project.id) + 1
    snapshot = create_project_snapshot(project)
    
    checkpoint = ProjectCheckpoint(
        project_id=project.id,
        version=version,
        snapshot=snapshot,
        created_by=user_id,
        message=message,
        total_points=total_points
    )
    db.add(checkpoint)
    db.flush()
    
    return checkpoint.version


async def restore_to_version(
    db: Session,
    project: Project,
    checkpoint_version: int,
    change_version: int = 0
):
    """
    Восстанавливает проект до указанной версии.
    """
    # Находим чекпоинт
    checkpoint = db.query(ProjectCheckpoint).filter(
        ProjectCheckpoint.project_id == project.id,
        ProjectCheckpoint.version == checkpoint_version
    ).first()
    
    if not checkpoint:
        raise HTTPException(status_code=404, detail="Checkpoint not found")
    
    # Берём базовый снимок
    snapshot = checkpoint.snapshot.copy()
    
    # Накатываем изменения если нужно
    if change_version > 0:
        changes = db.query(ProjectChange).filter(
            ProjectChange.project_id == project.id,
            ProjectChange.checkpoint_version == checkpoint_version,
            ProjectChange.change_version <= change_version
        ).order_by(ProjectChange.change_version.asc()).all()
        
        for change in changes:
            snapshot = apply_diff(snapshot, change.diff)
    
    # Применяем снимок к проекту
    for key, value in snapshot.items():
        if hasattr(project, key):
            # Пропускаем поля, которых нет в модели
            if key in ['approval_requested_at', 'approval_handled_at']:
                # Преобразуем строку ISO в datetime, если значение есть
                if value and isinstance(value, str):
                    try:
                        value = datetime.fromisoformat(value)
                    except (ValueError, TypeError):
                        value = None
                elif value is not None and not isinstance(value, datetime):
                    value = None
            setattr(project, key, value)
    
    # Сохраняем изменения
    db.flush()
    
    # Удаляем все последующие изменения в этом чекпоинте
    if change_version > 0:
        db.query(ProjectChange).filter(
            ProjectChange.project_id == project.id,
            ProjectChange.checkpoint_version == checkpoint_version,
            ProjectChange.change_version > change_version
        ).delete()
    else:
        db.query(ProjectChange).filter(
            ProjectChange.project_id == project.id,
            ProjectChange.checkpoint_version == checkpoint_version
        ).delete()
    
    # Удаляем все последующие чекпоинты
    db.query(ProjectCheckpoint).filter(
        ProjectCheckpoint.project_id == project.id,
        ProjectCheckpoint.version > checkpoint_version
    ).delete()
    
    # Удаляем изменения последующих чекпоинтов
    db.query(ProjectChange).filter(
        ProjectChange.project_id == project.id,
        ProjectChange.checkpoint_version > checkpoint_version
    ).delete()
    
    db.commit()
    db.refresh(project)
    
    return project


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

async def get_user_from_query_or_header(
    request: Request,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
) -> User:
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

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ РОЛЕВОЙ СИСТЕМЫ ====================
def count_participants_by_role(project: Project, role: str) -> int:
    if not project.participants:
        return 0
    return sum(1 for p in project.participants if p.get("role") == role)

def user_can_act_as_role(user: User, role: str) -> bool:
    if role == "executor":
        return True   
    if not user.is_teacher:
        return False
    if role == "curator":
        return user.teacher_info and user.teacher_info.get("curator", False)
    return role in user.teacher_info.get("roles", []) if user.teacher_info else False
def has_full_edit_permission(project: Project, user: User) -> bool:
    if user.is_admin or is_curator(user):
        return True
    role = get_participant_role(project, user.id)
    if role == ProjectRole.CUSTOMER.value:
        return True
    if role == ProjectRole.EXECUTOR.value:
        has_customer = any(p.get("role") == ProjectRole.CUSTOMER.value for p in (project.participants or []))
        has_curator = any(p.get("role") == ProjectRole.CURATOR.value for p in (project.participants or []))
        if not has_customer and not has_curator:
            return True
    return False

def is_project_participant(project: Project, user_id: int) -> bool:
    return any(p.get("user_id") == user_id for p in (project.participants or []))

def get_participant_role(project: Project, user_id: int) -> Optional[str]:
    for p in (project.participants or []):
        if p.get("user_id") == user_id:
            return p.get("role")
    return None

def get_approval_info(project: Project) -> dict:
    return {
        "is_approved": project.is_approved if hasattr(project, 'is_approved') else False,
        "approval_status": project.approval_status if hasattr(project, 'approval_status') else "draft",
        "approval_requested_at": project.approval_requested_at.isoformat() if hasattr(project, 'approval_requested_at') and project.approval_requested_at else None,
        "approval_requested_by": project.approval_requested_by if hasattr(project, 'approval_requested_by') else None,
        "approval_handled_at": project.approval_handled_at.isoformat() if hasattr(project, 'approval_handled_at') and project.approval_handled_at else None,
        "approval_handled_by": project.approval_handled_by if hasattr(project, 'approval_handled_by') else None,
        "approval_comment": project.approval_comment if hasattr(project, 'approval_comment') else None
    }

# ==================== ЭНДПОИНТЫ ВЕРСИОНИРОВАНИЯ ====================

@app.get("/projects/{project_id}/versions", tags=["Projects"])
async def get_project_versions(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Получить полную историю версий проекта.
    Возвращает все чекпоинты с их изменениями.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not (current_user.is_admin or is_curator(current_user) or is_project_participant(project, current_user.id)):
        raise HTTPException(status_code=403, detail="Only project participants can view versions")
    
    # Получаем все чекпоинты от новых к старым
    checkpoints = db.query(ProjectCheckpoint).filter(
        ProjectCheckpoint.project_id == project_id
    ).order_by(ProjectCheckpoint.version.desc()).all()
    
    result = []
    for cp in checkpoints:
        # Получаем изменения для этого чекпоинта
        changes = db.query(ProjectChange).filter(
            ProjectChange.project_id == project_id,
            ProjectChange.checkpoint_version == cp.version
        ).order_by(ProjectChange.change_version.asc()).all()
        
        checkpoint_data = {
            "version": str(cp.version),
            "is_current": False,
            "created_at": cp.created_at.isoformat() if cp.created_at else None,
            "created_by": cp.created_by,
            "message": cp.message,
            "total_points": cp.total_points,
            "changes_count": len(changes),
            "changes": [
                {
                    "version": f"{c.checkpoint_version}.{c.change_version}",
                    "checkpoint_version": c.checkpoint_version,
                    "change_version": c.change_version,
                    "type": c.change_type,
                    "points": c.points,
                    "description": c.description,
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                    "created_by": c.created_by
                }
                for c in changes
            ]
        }
        result.append(checkpoint_data)
    
    # Добавляем текущую версию (несохранённые изменения)
    current_cp_version = get_current_checkpoint_version(db, project_id)
    if current_cp_version > 0:
        current_changes = db.query(ProjectChange).filter(
            ProjectChange.project_id == project_id,
            ProjectChange.checkpoint_version == current_cp_version
        ).order_by(ProjectChange.change_version.asc()).all()
        
        current_points = sum(c.points for c in current_changes)
        
        result.insert(0, {
            "version": f"{current_cp_version}.{len(current_changes)} (current)",
            "is_current": True,
            "created_at": None,
            "created_by": None,
            "message": "Current state (not saved as checkpoint)",
            "total_points": current_points,
            "points_to_next_checkpoint": max(0, POINTS_THRESHOLD - current_points),
            "changes_count": len(current_changes),
            "changes": [
                {
                    "version": f"{c.checkpoint_version}.{c.change_version}",
                    "checkpoint_version": c.checkpoint_version,
                    "change_version": c.change_version,
                    "type": c.change_type,
                    "points": c.points,
                    "description": c.description,
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                    "created_by": c.created_by
                }
                for c in current_changes
            ]
        })
    
    return {
        "project_id": project_id,
        "points_threshold": POINTS_THRESHOLD,
        "checkpoints": result
    }


@app.post("/projects/{project_id}/checkpoint", tags=["Projects"])
async def create_manual_checkpoint(
    project_id: int,
    request: CreateCheckpointRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Создать ручной чекпоинт (точку сохранения).
    Доступно заказчику, куратору и админу.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not (current_user.is_admin or is_curator(current_user) or 
            get_participant_role(project, current_user.id) == ProjectRole.CUSTOMER.value):
        raise HTTPException(status_code=403, detail="Only customer, curator or admin can create checkpoints")
    
    total_points = get_total_points_since_last_checkpoint(db, project_id)
    version = await create_checkpoint(db, project, current_user.id, request.message, total_points)
    
    db.commit()
    
    return CreateCheckpointResponse(
        message=f"Checkpoint version {version} created successfully",
        version=version,
        total_points=total_points
    )


@app.post("/projects/{project_id}/restore/{checkpoint_version}", tags=["Projects"])
async def restore_project_version(
    project_id: int,
    checkpoint_version: int,
    change_version: int = Query(0, description="Номер изменения (0 = весь чекпоинт)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Восстановить проект до определённой версии.
    
    Примеры:
    - /restore/1/0 - восстановить до чекпоинта 1 (все изменения чекпоинта 1 будут удалены)
    - /restore/1/3 - восстановить до изменения 1.3 (изменения после 1.3 будут удалены)
    
    ВНИМАНИЕ: Все версии после указанной будут безвозвратно удалены!
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not (current_user.is_admin or is_curator(current_user) or 
            get_participant_role(project, current_user.id) == ProjectRole.CUSTOMER.value):
        raise HTTPException(status_code=403, detail="Only customer, curator or admin can restore versions")
    
    await restore_to_version(db, project, checkpoint_version, change_version)
    
    return RestoreVersionResponse(
        message=f"Project restored to version {checkpoint_version}.{change_version}",
        warning="All changes after this version have been permanently deleted"
    )


@app.delete("/projects/{project_id}/versions/{checkpoint_version}", tags=["Projects"])
async def delete_version(
    project_id: int,
    checkpoint_version: int,
    change_version: int = Query(0, description="0 = удалить весь чекпоинт, >0 = удалить конкретное изменение"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Удалить чекпоинт или конкретное изменение."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not (current_user.is_admin or is_curator(current_user)):
        raise HTTPException(status_code=403, detail="Only admins and curators can delete versions")
    
    if change_version == 0:
        # Удаляем весь чекпоинт
        total_checkpoints = db.query(ProjectCheckpoint).filter(
            ProjectCheckpoint.project_id == project_id
        ).count()
        
        # Проверяем, существует ли чекпоинт с таким номером
        checkpoint = db.query(ProjectCheckpoint).filter(
            ProjectCheckpoint.project_id == project_id,
            ProjectCheckpoint.version == checkpoint_version
        ).first()
        
        if not checkpoint:
            raise HTTPException(status_code=404, detail="Checkpoint not found")
        
        if total_checkpoints <= 1:
            raise HTTPException(status_code=400, detail="Cannot delete the last checkpoint")
        
        # Удаляем все изменения этого чекпоинта
        db.query(ProjectChange).filter(
            ProjectChange.project_id == project_id,
            ProjectChange.checkpoint_version == checkpoint_version
        ).delete()
        
        # Удаляем сам чекпоинт
        db.query(ProjectCheckpoint).filter(
            ProjectCheckpoint.project_id == project_id,
            ProjectCheckpoint.version == checkpoint_version
        ).delete()
        
        # Сдвигаем номера последующих чекпоинтов
        subsequent_checkpoints = db.query(ProjectCheckpoint).filter(
            ProjectCheckpoint.project_id == project_id,
            ProjectCheckpoint.version > checkpoint_version
        ).order_by(ProjectCheckpoint.version.asc()).all()
        
        for cp in subsequent_checkpoints:
            old_version = cp.version
            cp.version -= 1
            # Обновляем checkpoint_version в связанных изменениях
            db.query(ProjectChange).filter(
                ProjectChange.project_id == project_id,
                ProjectChange.checkpoint_version == old_version
            ).update({ProjectChange.checkpoint_version: cp.version})
        
        db.commit()
        
        return DeleteVersionResponse(
            message=f"Checkpoint {checkpoint_version} and all its changes deleted. Subsequent checkpoints renumbered."
        )
    else:
        # Удаляем конкретное изменение
        deleted = db.query(ProjectChange).filter(
            ProjectChange.project_id == project_id,
            ProjectChange.checkpoint_version == checkpoint_version,
            ProjectChange.change_version == change_version
        ).delete()
        
        if deleted == 0:
            raise HTTPException(status_code=404, detail="Change version not found")
        
        # Сдвигаем номера последующих изменений в этом чекпоинте
        subsequent_changes = db.query(ProjectChange).filter(
            ProjectChange.project_id == project_id,
            ProjectChange.checkpoint_version == checkpoint_version,
            ProjectChange.change_version > change_version
        ).order_by(ProjectChange.change_version.asc()).all()
        
        for c in subsequent_changes:
            c.change_version -= 1
        
        db.commit()
        
        return DeleteVersionResponse(
            message=f"Change {checkpoint_version}.{change_version} deleted. Subsequent changes renumbered."
        )

@app.get("/projects/{project_id}/version-stats", tags=["Projects"])
async def get_version_stats(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить статистику версионирования проекта."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Разрешаем доступ: админам, кураторам И участникам проекта
    if not (current_user.is_admin or is_curator(current_user) or is_project_participant(project, current_user.id)):
        raise HTTPException(status_code=403, detail="Only project participants, admins and curators can view stats")
    
    total_checkpoints = db.query(ProjectCheckpoint).filter(
        ProjectCheckpoint.project_id == project_id
    ).count()
    
    total_changes = db.query(ProjectChange).filter(
        ProjectChange.project_id == project_id
    ).count()
    
    current_version = get_current_checkpoint_version(db, project_id)
    current_points = get_total_points_since_last_checkpoint(db, project_id)
    
    # Собираем статистику по типам изменений
    change_stats = {}
    for change_type in CHANGE_POINTS.keys():
        count = db.query(ProjectChange).filter(
            ProjectChange.project_id == project_id,
            ProjectChange.change_type == change_type
        ).count()
        if count > 0:
            change_stats[change_type] = count
    
    progress_percent = min(100, round(current_points / POINTS_THRESHOLD * 100)) if POINTS_THRESHOLD > 0 else 0
    
    return {
        "project_id": project_id,
        "points_threshold": POINTS_THRESHOLD,
        "total_checkpoints": total_checkpoints,
        "total_changes": total_changes,
        "current_version": current_version,
        "current_points": current_points,
        "points_to_next_checkpoint": max(0, POINTS_THRESHOLD - current_points),
        "progress_percent": progress_percent,
        "change_stats": change_stats
    }

# ==================== ЭНД ТОКЕНОВ ====================
@app.post("/token", response_model=TokenResponse, tags=["Auth"])
@limiter.limit("5/minute")
async def token_login(
    request: Request,
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

    old_snapshot = create_project_snapshot(project)
    
    project.ignore_file_limits = not project.ignore_file_limits
    
    db.commit()
    db.refresh(project)
    
    new_snapshot = create_project_snapshot(project)
    diff = compute_project_diff(old_snapshot, new_snapshot)
    await record_change(db, project_id, "admin_toggle_file_limits", 3, diff,
                       admin.id, f"Admin toggled file limits")
    db.commit()
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

@app.delete("/users/me", tags=["Common"])
async def delete_my_account(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user_id = current_user.id
    if current_user.avatar:
        filepath = os.path.join(AVATAR_DIR, current_user.avatar)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError as e:
                print(f"Ошибка при удалении файла аватара {filepath}: {e}")
    
    all_projects = db.query(Project).all()
    for project in all_projects:
        if project.participants:
            project.participants = [
                p for p in project.participants 
                if p.get("user_id") != user_id
            ]
            flag_modified(project, "participants")
        if project.hidden_by_users and user_id in project.hidden_by_users:
            project.hidden_by_users.remove(user_id)
            flag_modified(project, "hidden_by_users")
        if project.hidden_by == user_id:
            project.hidden_by = None
    
    db.query(Invitation).filter(
        (Invitation.invited_user_id == user_id) | 
        (Invitation.invited_by == user_id)
    ).delete()
    
    user_files = db.query(ProjectFile).filter(
        ProjectFile.uploaded_by == user_id
    ).all()
    
    for file_record in user_files:
        file_path = os.path.join("uploads", file_record.filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError as e:
                print(f"Ошибка при удалении файла {file_path}: {e}")
        db.delete(file_record)
    
    try:
        for key in redis_client.scan_iter(f"refresh:{user_id}:*"):
            redis_client.delete(key)
    except Exception as e:
        print(f"Ошибка при удалении токенов из Redis: {e}")
    
    db.delete(current_user)
    db.commit()
    
    return {"message": f"Account {user_id} successfully deleted"}

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

    old_snapshot = create_project_snapshot(project)
    
    update_data = project_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(project, field):
            setattr(project, field, value)
    
    db.commit()
    db.refresh(project)
    
    new_snapshot = create_project_snapshot(project)
    diff = compute_project_diff(old_snapshot, new_snapshot)
    await record_change(db, project_id, "admin_update_project", 5, diff,
                       admin.id, f"Admin updated project")
    db.commit()
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

# ==================== ВЕРИФИКАЦИЯ EMAIL ====================
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
@limiter.limit("5/minute")
async def check_student_email(
    request: Request,
    body: dict
):
    email = body.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    if is_student_email_accepted(email):
        return {"accepted": True, "message": "Email разрешён для регистрации ученика"}
    else:
        raise HTTPException(
            status_code=403,
            detail="Этот email не разрешён для регистрации ученика. Используйте email с доменом lit1533.ru или из списка разрешённых."
        )

@app.get("/default-tasks", tags=["DefaultTasks"])
async def get_default_tasks(current_user: User = Depends(get_current_user)):
    return load_default_tasks()

# ==================== УЧЕНИКИ ====================
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
@limiter.limit("5/minute")
async def check_teacher_email(
    request: Request,
    body: dict
):
    email = body.get("email")
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
async def verify_and_create_teacher(request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    email = body.get("email")
    code = body.get("code")
    teacher_data = body.get("teacher_data")
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

    old_snapshot = create_project_snapshot(project)
    project.is_old = True
    db.commit()
    db.refresh(project)

    new_snapshot = create_project_snapshot(project)
    diff = compute_project_diff(old_snapshot, new_snapshot)
    await record_change(db, project_id, "project_mark_old", 5, diff,
                       current_user.id, f"Project marked as old by {current_user.nickname}")
    db.commit()
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

    old_snapshot = create_project_snapshot(project)
    project.is_old = False
    db.commit()
    db.refresh(project)

    new_snapshot = create_project_snapshot(project)
    diff = compute_project_diff(old_snapshot, new_snapshot)
    await record_change(db, project_id, "project_unmark_old", 5, diff,
                       current_user.id, f"Project unmarked as old by {current_user.nickname}")
    db.commit()
    return project
@app.post("/projects/{project_id}/join-requests", response_model=ProjectResponse, tags=["Projects"])
async def create_join_request(
    project_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        body = await request.json()
        requested_role = body.get("requested_role")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body, expected { 'requested_role': '...' }")

    if not requested_role:
        raise HTTPException(status_code=400, detail="Missing 'requested_role' field")
    if requested_role not in [r.value for r in ProjectRole]:
        raise HTTPException(status_code=400, detail=f"Invalid role. Allowed: {[r.value for r in ProjectRole]}")

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if any(p.get("user_id") == current_user.id for p in (project.participants or [])):
        raise HTTPException(status_code=400, detail="You are already a participant")

    if not user_can_act_as_role(current_user, requested_role):
        raise HTTPException(status_code=403, detail=f"You cannot act as {requested_role}")

    current_count = count_participants_by_role(project, requested_role)
    required = project.required_roles.get(requested_role, 0) if project.required_roles else 0
    deficit = max(0, required - current_count)
    if deficit <= 0:
        raise HTTPException(status_code=400, detail=f"No open positions for role {requested_role}")

    if project.join_requests:
        existing = next(
            (r for r in project.join_requests
             if r.get("user_id") == current_user.id and
                r.get("status") == "pending" and
                r.get("requested_role") == requested_role),
            None
        )
        if existing:
            raise HTTPException(status_code=400, detail="You already have a pending request for this role")

    old_snapshot = create_project_snapshot(project)

    new_request = {
        "id": str(uuid.uuid4()),
        "user_id": current_user.id,
        "created_at": datetime.utcnow().isoformat(),
        "status": "pending",
        "requested_role": requested_role
    }
    if project.join_requests is None:
        project.join_requests = []
    project.join_requests.append(new_request)
    flag_modified(project, "join_requests")
    db.commit()
    db.refresh(project)

    new_snapshot = create_project_snapshot(project)
    diff = compute_project_diff(old_snapshot, new_snapshot)
    await record_change(db, project_id, "join_request_create", 3, diff,
                       current_user.id, f"Join request created by {current_user.nickname}")
    db.commit()
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

    old_snapshot = create_project_snapshot(project)

    if current_user.is_admin or is_curator(current_user):
        project.is_hidden = not project.is_hidden
        if project.is_hidden:
            project.hidden_by = current_user.id
        else:
            project.hidden_by = None
    else:
        participant = next((p for p in project.participants if p.get("user_id") == current_user.id), None)
        if not participant or participant.get("role") != ProjectRole.CUSTOMER.value:
            raise HTTPException(status_code=403, detail="Only customer, curator or admin can hide/show projects")
        project.is_hidden = not project.is_hidden
        if project.is_hidden:
            project.hidden_by = current_user.id
        else:
            project.hidden_by = None

    db.commit()
    db.refresh(project)

    new_snapshot = create_project_snapshot(project)
    diff = compute_project_diff(old_snapshot, new_snapshot)
    await record_change(db, project_id, "project_hide_toggle", 5, diff,
                       current_user.id, f"Project visibility toggled by {current_user.nickname}")
    db.commit()
    return project

@app.patch("/projects/{project_id}/links", response_model=ProjectResponse, tags=["Projects"])
async def update_project_links(
    project_id: int,
    links_update: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.is_old and not (current_user.is_admin or is_curator(current_user)):
        raise HTTPException(status_code=403, detail="Старый проект нельзя редактировать")
    
    if not is_project_participant(project, current_user.id):
        raise HTTPException(status_code=403, detail="Только участники проекта могут изменять ссылки")
    
    old_snapshot = create_project_snapshot(project)
    
    if project.links is None:
        project.links = {}
    
    if "github" in links_update:
        if links_update["github"] is None:
            project.links.pop("github", None)
        else:
            project.links["github"] = links_update["github"]
    
    if "google_drive" in links_update:
        if links_update["google_drive"] is None:
            project.links.pop("google_drive", None)
        else:
            project.links["google_drive"] = links_update["google_drive"]
    
    flag_modified(project, "links")
    db.commit()
    db.refresh(project)
    
    new_snapshot = create_project_snapshot(project)
    diff = compute_project_diff(old_snapshot, new_snapshot)
    await record_change(db, project_id, "link_update", 1, diff, current_user.id,
                       f"Links updated by {current_user.nickname}")
    db.commit()
    return project

@app.delete("/projects/{project_id}/links/github", response_model=ProjectResponse, tags=["Projects"])
async def delete_github_link(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.is_old and not (current_user.is_admin or is_curator(current_user)):
        raise HTTPException(status_code=403, detail="Старый проект нельзя редактировать")
    
    if not is_project_participant(project, current_user.id):
        raise HTTPException(status_code=403, detail="Только участники проекта могут удалять ссылки")
    
    old_snapshot = create_project_snapshot(project)
    
    if project.links and "github" in project.links:
        del project.links["github"]
        flag_modified(project, "links")
        db.commit()
        db.refresh(project)
    
    new_snapshot = create_project_snapshot(project)
    diff = compute_project_diff(old_snapshot, new_snapshot)
    await record_change(db, project_id, "link_delete", 1, diff, current_user.id,
                       f"GitHub link deleted by {current_user.nickname}")
    db.commit()
    return project

@app.delete("/projects/{project_id}/links/google-drive", response_model=ProjectResponse, tags=["Projects"])
async def delete_google_drive_link(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.is_old and not (current_user.is_admin or is_curator(current_user)):
        raise HTTPException(status_code=403, detail="Старый проект нельзя редактировать")
    
    if not is_project_participant(project, current_user.id):
        raise HTTPException(status_code=403, detail="Только участники проекта могут удалять ссылки")
    
    old_snapshot = create_project_snapshot(project)
    
    if project.links and "google_drive" in project.links:
        del project.links["google_drive"]
        flag_modified(project, "links")
        db.commit()
        db.refresh(project)
    
    new_snapshot = create_project_snapshot(project)
    diff = compute_project_diff(old_snapshot, new_snapshot)
    await record_change(db, project_id, "link_delete", 1, diff, current_user.id,
                       f"Google Drive link deleted by {current_user.nickname}")
    db.commit()
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

    request_obj = None
    for r in (project.join_requests or []):
        if r.get("id") == request_id:
            request_obj = r
            break
    if not request_obj:
        raise HTTPException(status_code=404, detail="Join request not found")
    if request_obj.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Request already processed")

    requested_role = request_obj.get("requested_role")
    if not requested_role or requested_role not in [r.value for r in ProjectRole]:
        raise HTTPException(status_code=400, detail="Invalid role in request")

    current_count = count_participants_by_role(project, requested_role)
    required = project.required_roles.get(requested_role, 0) if project.required_roles else 0
    deficit = max(0, required - current_count)
    if deficit <= 0:
        raise HTTPException(status_code=400, detail=f"No open positions left for role {requested_role}")

    old_snapshot = create_project_snapshot(project)

    new_participant = {
        "user_id": request_obj["user_id"],
        "role": requested_role,
        "joined_at": datetime.utcnow().isoformat()
    }
    if project.participants is None:
        project.participants = []
    project.participants.append(new_participant)
    request_obj["status"] = "accepted"
    flag_modified(project, "join_requests")
    flag_modified(project, "participants")
    db.commit()
    db.refresh(project)

    new_snapshot = create_project_snapshot(project)
    diff = compute_project_diff(old_snapshot, new_snapshot)
    await record_change(db, project_id, "join_request_accept", 3, diff,
                       current_user.id, f"Join request accepted by {current_user.nickname}")
    db.commit()
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
    
    old_snapshot = create_project_snapshot(project)
    
    comment["hidden"] = False
    flag_modified(project, "comments")
    db.commit()
    db.refresh(project)
    
    new_snapshot = create_project_snapshot(project)
    diff = compute_project_diff(old_snapshot, new_snapshot)
    await record_change(db, project_id, "comment_restore", 1, diff, current_user.id,
                       f"Comment restored by {current_user.nickname}")
    db.commit()
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
    
    request_obj = None
    for r in (project.join_requests or []):
        if r.get("id") == request_id:
            request_obj = r
            break
    if not request_obj:
        raise HTTPException(status_code=404, detail="Join request not found")
    if request_obj.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Request already processed")

    old_snapshot = create_project_snapshot(project)
    
    request_obj["status"] = "rejected"
    flag_modified(project, "join_requests")
    db.commit()
    db.refresh(project)

    new_snapshot = create_project_snapshot(project)
    diff = compute_project_diff(old_snapshot, new_snapshot)
    await record_change(db, project_id, "join_request_reject", 3, diff,
                       current_user.id, f"Join request rejected by {current_user.nickname}")
    db.commit()
    return project

@app.post("/projects/{project_id}/leave", response_model=ProjectResponse, tags=["Projects"])
async def leave_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project: raise HTTPException(404)
    if not is_project_participant(project, current_user.id): raise HTTPException(400, "Not a participant")
    if len(project.participants or []) == 1: raise HTTPException(400, "Cannot leave as only participant")
    
    old_snapshot = create_project_snapshot(project)
    user_role = get_participant_role(project, current_user.id)
    
    if project.participants:
        project.participants = [p for p in project.participants if p.get("user_id") != current_user.id]
        flag_modified(project, "participants")
    
    if user_role == ProjectRole.CUSTOMER.value:
        has_customer = any(p.get("role") == ProjectRole.CUSTOMER.value for p in (project.participants or []))
        if not has_customer and project.participants:
            project.participants[0]["role"] = ProjectRole.CUSTOMER.value
            flag_modified(project, "participants")
    
    if current_user.id in (project.hidden_by_users or []):
        project.hidden_by_users.remove(current_user.id)
        flag_modified(project, "hidden_by_users")
    
    db.commit(); db.refresh(project)
    new_snapshot = create_project_snapshot(project)
    await record_change(db, project_id, "participant_remove", 5,
                       compute_project_diff(old_snapshot, new_snapshot),
                       current_user.id, f"User {current_user.nickname} left project")
    db.commit()
    return project

@app.post("/projects/", response_model=ProjectResponse, tags=["Projects"])
async def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if project.required_roles is None:
        project.required_roles = {}

    creator_in_participants = any(p.user_id == current_user.id for p in project.participants)
    if not creator_in_participants:
        if not current_user.is_teacher:
            default_role = ProjectRole.CUSTOMER
        else:
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
        required_roles=project.required_roles,
        is_hidden=False,
        hidden_by=None,
        hidden_by_users=[],
        is_old=False,
        ignore_file_limits=False,
        is_approved=False,
        approval_status="draft",
        approval_requested_at=None,
        approval_requested_by=None,
        approval_handled_at=None,
        approval_handled_by=None,
        approval_comment=None
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    
    snapshot = create_project_snapshot(db_project)
    await create_checkpoint(db, db_project, current_user.id, "Project created", 10)
    await record_change(db, db_project.id, "project_create", 10, snapshot,
                       current_user.id, f"Project created by {current_user.nickname}")
    db.commit()
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
        raise HTTPException(status_code=403, detail="Старый проект нельзя редактировать")

    participant_role = get_participant_role(project, current_user.id)

    if not (current_user.is_admin or is_curator(current_user)):
        if participant_role not in [ProjectRole.CUSTOMER.value, ProjectRole.EXECUTOR.value]:
            raise HTTPException(status_code=403, detail="Only customer, executor, curator or admin can update the project")

    old_snapshot = create_project_snapshot(project)
    full_edit = has_full_edit_permission(project, current_user)

    if not full_edit and not (current_user.is_admin or is_curator(current_user)):
        update_data = project_update.model_dump(exclude_unset=True)
        allowed_fields = {'tasks', 'links'}
        filtered_update = {k: v for k, v in update_data.items() if k in allowed_fields}
        if not filtered_update:
            return project

        if 'tasks' in filtered_update:
            new_tasks = filtered_update['tasks']
            old_tasks = project.tasks or []
            titles = [task.get('title', '').strip().lower() for task in new_tasks if task.get('title')]
            if len(titles) != len(set(titles)):
                raise HTTPException(400, "Task titles must be unique")
            for i, new_task in enumerate(new_tasks):
                old_task = old_tasks[i] if i < len(old_tasks) else None
                if old_task and old_task.get("status") != "выполнена" and new_task.get("status") == "выполнена":
                    required_files = new_task.get("required_files", [])
                    for req in required_files:
                        req_id = req.get("id")
                        if not req_id: continue
                        attached = db.query(ProjectFile).filter(
                            ProjectFile.project_id == project_id, ProjectFile.task_id == i,
                            ProjectFile.required_file_id == req_id, ProjectFile.is_deleted == False
                        ).first()
                        if not attached:
                            raise HTTPException(401, f"Нужен файл: {req.get('name')}")
                if "attachments" not in new_task and old_task and "attachments" in old_task:
                    new_task["attachments"] = old_task["attachments"]
            project.tasks = new_tasks
            flag_modified(project, "tasks")
        if 'links' in filtered_update:
            project.links = filtered_update['links']
            flag_modified(project, "links")

        db.commit(); db.refresh(project)
        new_snapshot = create_project_snapshot(project)
        await record_change(db, project_id, "project_full_update", 5,
                           compute_project_diff(old_snapshot, new_snapshot),
                           current_user.id, f"Project updated by {current_user.nickname}")
        db.commit()
        return project

    if project_update.required_roles is not None:
        if not (current_user.is_admin or is_curator(current_user)):
            if participant_role != ProjectRole.CUSTOMER.value:
                raise HTTPException(403, "Only customer, curator or admin can change required roles")
        for role, count in project_update.required_roles.items():
            if role not in [r.value for r in ProjectRole]:
                raise HTTPException(400, f"Invalid role '{role}'")
            if not isinstance(count, int) or count < 0:
                raise HTTPException(400, f"Count must be non-negative")
        project.required_roles = project_update.required_roles
        flag_modified(project, "required_roles")

    if project_update.title is not None: project.title = project_update.title
    if project_update.body is not None: project.body = project_update.body
    if project_update.underbody is not None: project.underbody = project_update.underbody

    if project_update.tasks is not None:
        old_tasks = project.tasks or []
        new_tasks = project_update.tasks
        titles = [task.get('title', '').strip().lower() for task in new_tasks if task.get('title')]
        if len(titles) != len(set(titles)):
            raise HTTPException(400, "Task titles must be unique")
        for i, new_task in enumerate(new_tasks):
            old_task = old_tasks[i] if i < len(old_tasks) else None
            if old_task and old_task.get("status") != "выполнена" and new_task.get("status") == "выполнена":
                required_files = new_task.get("required_files", [])
                for req in required_files:
                    req_id = req.get("id")
                    if not req_id: continue
                    attached = db.query(ProjectFile).filter(
                        ProjectFile.project_id == project_id, ProjectFile.task_id == i,
                        ProjectFile.required_file_id == req_id, ProjectFile.is_deleted == False
                    ).first()
                    if not attached:
                        raise HTTPException(401, f"Нужен файл: {req.get('name')}")
            if "attachments" not in new_task and old_task and "attachments" in old_task:
                new_task["attachments"] = old_task["attachments"]
        project.tasks = new_tasks
        flag_modified(project, "tasks")

    if project_update.links is not None: project.links = project_update.links; flag_modified(project, "links")
    if project_update.comments is not None: project.comments = [c.model_dump(mode='json') for c in project_update.comments]; flag_modified(project, "comments")
    if project_update.participants is not None:
        new_ids = [p.user_id for p in project_update.participants]
        users = db.query(User).filter(User.id.in_(new_ids)).all()
        if len(users) != len(new_ids): raise HTTPException(404, "Users not found")
        project.participants = [p.model_dump(mode='json') for p in project_update.participants]
        flag_modified(project, "participants")

    db.commit(); db.refresh(project)
    new_snapshot = create_project_snapshot(project)
    await record_change(db, project_id, "project_full_update", 5,
                       compute_project_diff(old_snapshot, new_snapshot),
                       current_user.id, f"Project updated by {current_user.nickname}")
    db.commit()
    return project

@app.patch("/projects/{project_id}/tasks", response_model=ProjectResponse, tags=["Projects"])
async def update_project_tasks(
    project_id: int,
    tasks: List[Dict[str, Any]] = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    
    if project.is_old and not (current_user.is_admin or is_curator(current_user)):
        raise HTTPException(403, "Старый проект нельзя редактировать")
    
    participant_role = get_participant_role(project, current_user.id)
    allowed_roles = [ProjectRole.CUSTOMER.value, ProjectRole.EXECUTOR.value, ProjectRole.CURATOR.value]
    if not (current_user.is_admin or is_curator(current_user) or participant_role in allowed_roles):
        raise HTTPException(403, "Недостаточно прав для изменения задач")
    
    titles = [task.get('title', '').strip().lower() for task in tasks if task.get('title')]
    if len(titles) != len(set(titles)):
        raise HTTPException(400, "Task titles must be unique within a project")
    
    old_snapshot = create_project_snapshot(project)
    
    old_tasks = project.tasks or []
    for i, new_task in enumerate(tasks):
        old_task = old_tasks[i] if i < len(old_tasks) else None
        if old_task and old_task.get("status") != "выполнена" and new_task.get("status") == "выполнена":
            required_files = new_task.get("required_files", [])
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
                    raise HTTPException(401, f"Для завершения задачи '{new_task.get('title')}' необходимо прикрепить файл: {req.get('name')}")
        if "attachments" not in new_task and old_task and "attachments" in old_task:
            new_task["attachments"] = old_task["attachments"]
    
    project.tasks = tasks
    flag_modified(project, "tasks")
    db.commit()
    db.refresh(project)
    
    new_snapshot = create_project_snapshot(project)
    diff = compute_project_diff(old_snapshot, new_snapshot)
    await record_change(db, project_id, "tasks_bulk_update", 3, diff, current_user.id,
                       f"Tasks updated by {current_user.nickname}")
    db.commit()
    return project

@app.patch("/projects/{project_id}/subtasks/move", response_model=ProjectResponse, tags=["Projects"])
async def move_subtask(
    project_id: int,
    data: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    
    participant_role = get_participant_role(project, current_user.id)
    if not (current_user.is_admin or is_curator(current_user) or participant_role in [
        ProjectRole.CUSTOMER.value, 
        ProjectRole.EXECUTOR.value,
        ProjectRole.SUPERVISOR.value,
        ProjectRole.EXPERT.value
    ]):
        raise HTTPException(403, "Not enough permissions to move subtasks")
    
    if project.is_old and not (current_user.is_admin or is_curator(current_user)):
        raise HTTPException(403, "Cannot modify old project")
    
    from_task_idx = data.get("from_task_index")
    from_subtask_idx = data.get("from_subtask_index")
    to_task_idx = data.get("to_task_index")
    to_subtask_idx = data.get("to_subtask_index")
    
    if any(x is None for x in [from_task_idx, from_subtask_idx, to_task_idx, to_subtask_idx]):
        raise HTTPException(400, "Missing required fields")
    
    old_snapshot = create_project_snapshot(project)
    
    tasks = project.tasks or []
    
    if from_task_idx < 0 or from_task_idx >= len(tasks):
        raise HTTPException(400, "Invalid from_task_index")
    if to_task_idx < 0 or to_task_idx >= len(tasks):
        raise HTTPException(400, "Invalid to_task_index")
    
    from_task = tasks[from_task_idx]
    to_task = tasks[to_task_idx]
    
    from_subtasks = from_task.get("subtasks", [])
    to_subtasks = to_task.get("subtasks", [])
    
    if from_subtask_idx < 0 or from_subtask_idx >= len(from_subtasks):
        raise HTTPException(400, "Invalid from_subtask_index")
    
    moved_subtask = from_subtasks.pop(from_subtask_idx)
    insert_idx = min(to_subtask_idx, len(to_subtasks))
    to_subtasks.insert(insert_idx, moved_subtask)
    
    tasks[from_task_idx]["subtasks"] = from_subtasks
    tasks[to_task_idx]["subtasks"] = to_subtasks
    
    project.tasks = tasks
    flag_modified(project, "tasks")
    db.commit()
    db.refresh(project)
    
    new_snapshot = create_project_snapshot(project)
    diff = compute_project_diff(old_snapshot, new_snapshot)
    await record_change(db, project_id, "subtask_move", 1, diff, current_user.id,
                       f"Subtask moved by {current_user.nickname}")
    db.commit()
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
    
    old_snapshot = create_project_snapshot(project)
    
    if project.comments is None:
        project.comments = []
    comment.authorId = current_user.id
    comment.authorRole = get_author_role(current_user, project)
    project.comments.append(comment.model_dump(mode='json'))
    flag_modified(project, "comments")
    
    try:
        db.commit()
        db.refresh(project)
        
        new_snapshot = create_project_snapshot(project)
        diff = compute_project_diff(old_snapshot, new_snapshot)
        await record_change(db, project_id, "comment_add", 1, diff, current_user.id,
                           f"Comment added by {current_user.nickname}")
        db.commit()
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
        old_snapshot = create_project_snapshot(project)
        try:
            invitations = db.query(Invitation).filter(Invitation.project_id == project_id).all()
            for invitation in invitations:
                db.delete(invitation)
            
            files = db.query(ProjectFile).filter(ProjectFile.project_id == project_id).all()
            for f in files:
                file_path = os.path.join("uploads", f.filename)
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except OSError as e:
                        print(f"Error deleting file {file_path}: {e}")
                db.delete(f)
            
            db.delete(project)
            db.commit()
            
            await record_change(db, project_id, "admin_delete_project", 10, old_snapshot,
                               current_user.id, f"Admin permanently deleted project '{old_snapshot.get('title')}'")
            return {"message": f"Project {project_id} permanently deleted successfully"}
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error deleting project: {str(e)}")
    
    participant = next((p for p in project.participants if p.get("user_id") == current_user.id), None)
    if not participant or participant.get("role") != ProjectRole.CUSTOMER.value:
        raise HTTPException(status_code=403, detail="Only customer, curator or admin can delete/hide the project")
    
    old_snapshot = create_project_snapshot(project)
    
    if current_user.id not in project.hidden_by_users:
        project.hidden_by_users.append(current_user.id)
    if not project.is_hidden:
        project.is_hidden = True
        project.hidden_by = current_user.id
    flag_modified(project, "hidden_by_users")
    db.commit()
    db.refresh(project)
    
    new_snapshot = create_project_snapshot(project)
    diff = compute_project_diff(old_snapshot, new_snapshot)
    await record_change(db, project_id, "project_hide_toggle", 5, diff,
                       current_user.id, f"Project hidden by {current_user.nickname}")
    db.commit()
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
    
    old_snapshot = create_project_snapshot(project)
    
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
        
        new_snapshot = create_project_snapshot(project)
        diff = compute_project_diff(old_snapshot, new_snapshot)
        await record_change(db, project_id, "task_comment_add", 1, diff, current_user.id,
                           f"Task comment added by {current_user.nickname}")
        db.commit()
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

    old_snapshot = create_project_snapshot(project)

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

    new_snapshot = create_project_snapshot(project)
    diff = compute_project_diff(old_snapshot, new_snapshot)
    await record_change(db, project_id, "suggestion_create", 3, diff,
                       current_user.id, f"Suggestion created by {current_user.nickname}")
    db.commit()
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
    
    user_role = get_participant_role(project, current_user.id)
    if not (current_user.is_admin or is_curator(current_user)):
        if user_role != ProjectRole.CUSTOMER.value:
            raise HTTPException(status_code=403, detail="Only customer, curator or admin can accept suggestions")

    old_snapshot = create_project_snapshot(project)
    
    suggestion["status"] = SuggestionStatus.ACCEPTED.value
    flag_modified(project, "suggestions")
    
    if (user_role == ProjectRole.CUSTOMER.value or current_user.is_admin or is_curator(current_user)) and suggestion["target_type"] == "project":
        for key, value in suggestion["changes"].items():
            if hasattr(project, key):
                setattr(project, key, value)
    
    db.commit()
    db.refresh(project)

    new_snapshot = create_project_snapshot(project)
    diff = compute_project_diff(old_snapshot, new_snapshot)
    await record_change(db, project_id, "suggestion_accept", 3, diff,
                       current_user.id, f"Suggestion accepted by {current_user.nickname}")
    db.commit()
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
        if role != ProjectRole.CUSTOMER.value:
            raise HTTPException(status_code=403, detail="Only customer, curator or admin can reject suggestions")

    old_snapshot = create_project_snapshot(project)
    
    suggestion["status"] = SuggestionStatus.REJECTED.value
    flag_modified(project, "suggestions")
    db.commit()
    db.refresh(project)

    new_snapshot = create_project_snapshot(project)
    diff = compute_project_diff(old_snapshot, new_snapshot)
    await record_change(db, project_id, "suggestion_reject", 3, diff,
                       current_user.id, f"Suggestion rejected by {current_user.nickname}")
    db.commit()
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

# ==================== ПРИГЛАШЕНИЯ ====================
@app.post("/projects/{project_id}/invite", response_model=Dict[str, str], tags=["Projects"])
async def create_invitation_by_email(
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
async def accept_invitation_by_token(
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
    role = data["role"]
    current_count = count_participants_by_role(project, role)
    required = project.required_roles.get(role, 0) if project.required_roles else 0
    deficit = max(0, required - current_count)
    if deficit <= 0:
        raise HTTPException(status_code=400, detail=f"No open positions for role {role}. Cannot accept invitation.")
    new_participant = {
        "user_id": current_user.id,
        "role": role,
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
    
    old_snapshot = create_project_snapshot(project)
    
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

    compressible_gzip = ["text/plain", "application/msword", "application/vnd.ms-powerpoint"]
    image_compressible = ["image/png", "image/jpeg"]

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
            print(f"Image compression failed: {e}")

    file_path = os.path.join("uploads", final_filename)
    with open(file_path, "wb") as f:
        f.write(final_content)

    db_file = ProjectFile(
        project_id=project_id, task_id=task_id, filename=final_filename,
        required_file_id=required_file_id, original_filename=file.filename,
        file_size=len(contents), mime_type=file.content_type,
        uploaded_by=current_user.id, compressed=compressed or compressed_image
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)

    if task_id is not None:
        task = project.tasks[task_id]
        if "attachments" not in task:
            task["attachments"] = []
        attachment = {
            "id": str(uuid.uuid4()), "file_id": db_file.id,
            "required_file_id": required_file_id, "uploaded_at": datetime.utcnow().isoformat(),
            "original_filename": file.filename, "size": len(contents), "mime_type": file.content_type
        }
        task["attachments"].append(attachment)
        flag_modified(project, "tasks")
        db.commit()
    
    db.refresh(project)
    new_snapshot = create_project_snapshot(project)
    diff = compute_project_diff(old_snapshot, new_snapshot)
    await record_change(db, project_id, "file_upload", 3, diff, current_user.id,
                       f"File '{file.filename}' uploaded by {current_user.nickname}")
    db.commit()
    return db_file

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
    if not (current_user.id == file_record.uploaded_by or current_user.is_admin or 
            is_curator(current_user) or is_project_participant(project, current_user.id)):
        raise HTTPException(403, "Not enough permissions")
    
    old_snapshot = create_project_snapshot(project)
    
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
    db.refresh(project)
    
    new_snapshot = create_project_snapshot(project)
    diff = compute_project_diff(old_snapshot, new_snapshot)
    await record_change(db, project.id, "file_delete", 3, diff, current_user.id,
                       f"File '{file_record.original_filename}' deleted by {current_user.nickname}")
    db.commit()
    return {"message": "File deleted"}
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

    if not (current_user.is_admin or is_curator(current_user) or is_project_participant(project, current_user.id)):
        if not project.is_old:
            raise HTTPException(403, "Not enough permissions")

    query = db.query(ProjectFile).filter(
        ProjectFile.project_id == project_id,
        ProjectFile.is_deleted == False
    )
    if task_id is not None:
        query = query.filter(ProjectFile.task_id == task_id)

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
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")

    old_snapshot = create_project_snapshot(project)
    
    files = db.query(ProjectFile).filter(
        ProjectFile.project_id == project_id,
        ProjectFile.is_deleted == False
    ).all()

    for f in files:
        file_path = os.path.join("uploads", f.filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError as e:
                print(f"Ошибка удаления файла {file_path}: {e}")
        db.delete(f)

    if project.tasks:
        for task in project.tasks:
            if "attachments" in task:
                task["attachments"] = []
        flag_modified(project, "tasks")

    db.commit()
    db.refresh(project)
    
    new_snapshot = create_project_snapshot(project)
    diff = compute_project_diff(old_snapshot, new_snapshot)
    await record_change(db, project_id, "admin_delete_all_files", 10, diff,
                       admin.id, f"Admin deleted all files ({len(files)} files)")
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
@limiter.limit("2/minute")
async def request_verification_code(
    request: Request,
    body: dict,
    db: Session = Depends(get_db)
):
    email = body.get("email")
    is_teacher = body.get("is_teacher", False)
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
@limiter.limit("2/minute")
async def request_verification(request: Request, body: EmailVerificationCodeRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_verified:
        raise HTTPException(status_code=400, detail="Email already verified")
    code = generate_verification_code()
    redis_client.setex(f"verify:{body.email}", 600, code)
    await send_verification_email(body.email, code)
    return {"message": "Verification code sent"}

@app.post("/auth/verify-email", tags=["Auth"])
@limiter.limit("5/minute")
async def verify_email(
    request: Request,
    body: dict,
    db: Session = Depends(get_db)
):
    email = body.get("email")
    code = body.get("code")
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
@limiter.limit("2/minute")
async def register_with_verification(
    request: Request,
    db: Session = Depends(get_db)
):
    body = await request.json()
    email = body.get("email")
    code = body.get("code")
    user_data = body.get("user_data")
    is_teacher = body.get("is_teacher", False)
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
@limiter.limit("5/minute")
async def auth_login(request: Request, credentials: LoginRequest, db: Session = Depends(get_db)):
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
@limiter.limit("10/minute")
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
@limiter.limit("10/minute")
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
    
    old_snapshot = create_project_snapshot(project)
    
    comment["hidden"] = True
    flag_modified(project, "comments")
    db.commit()
    db.refresh(project)
    
    new_snapshot = create_project_snapshot(project)
    diff = compute_project_diff(old_snapshot, new_snapshot)
    await record_change(db, project_id, "comment_delete", 1, diff, current_user.id,
                       f"Comment hidden by {current_user.nickname}")
    db.commit()
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
    
    old_snapshot = create_project_snapshot(project)
    
    comment["hidden"] = True
    flag_modified(project, "tasks")
    db.commit()
    db.refresh(project)
    
    new_snapshot = create_project_snapshot(project)
    diff = compute_project_diff(old_snapshot, new_snapshot)
    await record_change(db, project_id, "task_comment_delete", 1, diff, current_user.id,
                       f"Task comment hidden by {current_user.nickname}")
    db.commit()
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
        if role not in [ProjectRole.CUSTOMER.value, ProjectRole.SUPERVISOR.value]:
            raise HTTPException(403, "Only customer, supervisor, curator or admin can invite")
    invited_user = db.query(User).filter(User.id == invite.invited_user_id).first()
    if not invited_user:
        raise HTTPException(404, "User not found")
    if any(p.get("user_id") == invite.invited_user_id for p in (project.participants or [])):
        raise HTTPException(400, "User is already a participant")
    current_count = count_participants_by_role(project, invite.role.value)
    required = project.required_roles.get(invite.role.value, 0) if project.required_roles else 0
    deficit = max(0, required - current_count)
    if deficit <= 0:
        raise HTTPException(400, f"No open positions for role {invite.role.value}")
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
    current_count = count_participants_by_role(project, invite.role)
    required = project.required_roles.get(invite.role, 0) if project.required_roles else 0
    deficit = max(0, required - current_count)
    if deficit <= 0:
        raise HTTPException(400, f"No open positions for role {invite.role}. Cannot accept invitation.")
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

# ==================== СИСТЕМА ЗАЯВОК НА ПУБЛИКАЦИЮ ПРОЕКТА ====================

@app.post("/projects/{project_id}/request-approval", response_model=ProjectResponse, tags=["Projects"])
async def request_project_approval(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    participant_role = get_participant_role(project, current_user.id)
    can_request = (current_user.is_admin or is_curator(current_user) or participant_role == ProjectRole.CUSTOMER.value)
    if not can_request:
        raise HTTPException(status_code=403, detail="Only project customer, curator or admin can request approval")
    
    if not hasattr(project, 'approval_status'):
        project.approval_status = "draft"
    if project.approval_status == "pending":
        raise HTTPException(status_code=400, detail="Project already pending approval")
    if project.approval_status == "approved":
        raise HTTPException(status_code=400, detail="Project already approved")
    if not project.title or not project.body:
        raise HTTPException(status_code=400, detail="Project must have title and body")

    old_snapshot = create_project_snapshot(project)
    
    project.approval_status = "pending"
    project.is_approved = False
    project.approval_requested_at = datetime.utcnow()
    project.approval_requested_by = current_user.id
    project.approval_handled_at = None
    project.approval_handled_by = None
    project.approval_comment = None
    
    db.commit()
    db.refresh(project)

    new_snapshot = create_project_snapshot(project)
    diff = compute_project_diff(old_snapshot, new_snapshot)
    await record_change(db, project_id, "project_approval_request", 5, diff,
                       current_user.id, f"Approval requested by {current_user.nickname}")
    db.commit()
    return project

@app.get("/projects/{project_id}/is-approved", tags=["Projects"])
async def check_project_approved(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Проверка, одобрен ли проект. Возвращает простой boolean."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Проверяем разные возможные поля
    is_approved = False
    if hasattr(project, 'is_approved') and project.is_approved:
        is_approved = True
    elif hasattr(project, 'approval_info') and project.approval_info and project.approval_info.get('is_approved'):
        is_approved = True
    
    return {"is_approved": is_approved, "status": getattr(project, 'approval_status', 'draft')}

@app.post("/projects/{project_id}/cancel-approval", response_model=ProjectResponse, tags=["Projects"])
async def cancel_project_approval(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    participant_role = get_participant_role(project, current_user.id)
    can_cancel = (current_user.is_admin or is_curator(current_user) or participant_role == ProjectRole.CUSTOMER.value)
    if not can_cancel:
        raise HTTPException(status_code=403, detail="Only customer, curator or admin can cancel")
    
    if not hasattr(project, 'approval_status') or project.approval_status != "pending":
        raise HTTPException(status_code=400, detail=f"Cannot cancel with status: {getattr(project, 'approval_status', 'draft')}")

    old_snapshot = create_project_snapshot(project)
    
    project.approval_status = "draft"
    project.is_approved = False
    project.approval_requested_at = None
    project.approval_requested_by = None
    
    db.commit()
    db.refresh(project)

    new_snapshot = create_project_snapshot(project)
    diff = compute_project_diff(old_snapshot, new_snapshot)
    await record_change(db, project_id, "project_approval_cancel", 5, diff,
                       current_user.id, f"Approval cancelled by {current_user.nickname}")
    db.commit()
    return project


@app.post("/admin/projects/{project_id}/request-approval", response_model=ProjectResponse, tags=["Admin"])
async def admin_request_approval(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Административный эндпоинт для отправки заявки на публикацию от имени любого проекта."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not hasattr(project, 'approval_status'):
        project.approval_status = "draft"
    
    if project.approval_status == "pending":
        raise HTTPException(status_code=400, detail="Project already pending approval")
    if project.approval_status == "approved":
        raise HTTPException(status_code=400, detail="Project already approved")
    
    if not project.title or not project.body:
        raise HTTPException(
            status_code=400, 
            detail="Project must have title and body before requesting approval"
        )
    
    project.approval_status = "pending"
    project.is_approved = False
    project.approval_requested_at = datetime.utcnow()
    project.approval_requested_by = current_user.id
    project.approval_handled_at = None
    project.approval_handled_by = None
    project.approval_comment = None
    
    db.commit()
    db.refresh(project)
    
    return project


@app.get("/admin/approval-requests", tags=["Admin"])
async def get_approval_requests(
    status_filter: Optional[str] = Query(None, description="Фильтр: pending, approved, rejected"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получение списка заявок на публикацию."""
    if not (current_user.is_admin or is_curator(current_user)):
        raise HTTPException(status_code=403, detail="Only admins and curators can view approval requests")
    
    query = db.query(Project)
    
    if status_filter:
        query = query.filter(Project.approval_status == status_filter)
    
    projects = query.all()
    
    result = {
        "pending": [],
        "approved": [],
        "rejected": []
    }
    
    for project in projects:
        customer = None
        for p in (project.participants or []):
            if p.get("role") == ProjectRole.CUSTOMER.value:
                user = db.query(User).filter(User.id == p.get("user_id")).first()
                if user:
                    customer = user
                break
        
        requester = db.query(User).filter(User.id == project.approval_requested_by).first() if hasattr(project, 'approval_requested_by') and project.approval_requested_by else None
        
        requester_role = "Unknown"
        if requester:
            if requester.is_admin:
                requester_role = "Admin"
            elif is_curator(requester):
                requester_role = "Curator"
            else:
                requester_role = "Customer"
        
        approval_data = {
            "project_id": project.id,
            "project_title": project.title,
            "requested_by": getattr(project, 'approval_requested_by', None),
            "requested_by_name": requester.fullname if requester else "Unknown",
            "requested_by_role": requester_role,
            "requested_at": project.approval_requested_at.isoformat() if hasattr(project, 'approval_requested_at') and project.approval_requested_at else None,
            "status": getattr(project, 'approval_status', 'draft'),
            "customer_name": customer.fullname if customer else "No customer assigned"
        }
        
        status = approval_data["status"] if approval_data["status"] in result else "pending"
        result[status].append(approval_data)
    
    return result


@app.post("/projects/{project_id}/approve", response_model=ProjectResponse, tags=["Projects"])
async def approve_project(
    project_id: int,
    action: ApprovalAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not (current_user.is_admin or is_curator(current_user)):
        raise HTTPException(status_code=403, detail="Only admins and curators can approve/reject projects")
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not hasattr(project, 'approval_status') or project.approval_status != "pending":
        raise HTTPException(status_code=400, detail=f"Cannot process with status: {getattr(project, 'approval_status', 'draft')}")
    
    if action.action not in ["approve", "reject"]:
        raise HTTPException(status_code=400, detail="Action must be 'approve' or 'reject'")

    old_snapshot = create_project_snapshot(project)
    
    project.approval_handled_at = datetime.utcnow()
    project.approval_handled_by = current_user.id
    project.approval_comment = action.comment
    
    if action.action == "approve":
        project.approval_status = "approved"
        project.is_approved = True
    else:
        project.approval_status = "rejected"
        project.is_approved = False
    
    db.commit()
    db.refresh(project)

    new_snapshot = create_project_snapshot(project)
    diff = compute_project_diff(old_snapshot, new_snapshot)
    await record_change(db, project_id, "project_approval_decision", 5, diff,
                       current_user.id, f"Project {action.action}d by {current_user.nickname}")
    db.commit()
    return project


@app.get("/projects/{project_id}/approval-status", tags=["Projects"])
async def get_approval_status(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получение статуса заявки проекта."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not (current_user.is_admin or 
            is_curator(current_user) or 
            is_project_participant(project, current_user.id)):
        raise HTTPException(status_code=403, detail="Only project participants can view approval status")
    
    requester = db.query(User).filter(User.id == project.approval_requested_by).first() if hasattr(project, 'approval_requested_by') and project.approval_requested_by else None
    handler = db.query(User).filter(User.id == project.approval_handled_by).first() if hasattr(project, 'approval_handled_by') and project.approval_handled_by else None
    
    return {
        "approval_info": get_approval_info(project),
        "requester_name": requester.fullname if requester else None,
        "handler_name": handler.fullname if handler else None,
        "status": getattr(project, 'approval_status', 'draft')
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)