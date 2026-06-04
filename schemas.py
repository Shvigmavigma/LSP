from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class JoinRequest(BaseModel):
    id: str
    user_id: int
    created_at: datetime
    status: str 

# ---------- СХЕМА КОММЕНТОВ ----------
class Comment(BaseModel):
    id: str
    authorId: int
    content: str
    authorRole: Optional[str] = None   
    createdAt: str
    isRead: bool
    hidden: bool = False      

# ---------- РОЛИ В ПРОЕКТАХ ----------
class ProjectRole(str, Enum):
    CUSTOMER = "customer"      # Заказчик
    SUPERVISOR = "supervisor"   # Научный руководитель
    EXPERT = "expert"           # Эксперт
    EXECUTOR = "executor"       # Исполнитель
    CURATOR = "curator"         # Куратор

# ---------- Participant ----------
class Participant(BaseModel):
    user_id: int
    role: ProjectRole
    joined_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    invited_by: Optional[int] = None 

# ---------- общая база ----------
class UserBase(BaseModel):
    nickname: str
    fullname: str
    email: EmailStr
    avatar: Optional[str] = None
    speciality: Optional[str] = None
    is_teacher: bool = False  

# ---------- ученик ----------
class StudentBase(UserBase):
    class_: float = Field(
        0.0,
        alias="class",
        validation_alias="class",
        serialization_alias="class"
    )
    is_teacher: bool = False 

class StudentCreate(StudentBase):
    password: str
    
    @field_validator('is_teacher')
    def validate_is_teacher(cls, v):
        if v is True:
            raise ValueError('Student cannot be a teacher')
        return v

class StudentResponse(StudentBase):
    id: int
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class StudentUpdate(BaseModel):
    fullname: Optional[str] = None
    email: Optional[EmailStr] = None
    class_: Optional[float] = Field(None, alias="class")
    speciality: Optional[str] = None
    avatar: Optional[str] = None
    model_config = ConfigDict(populate_by_name=True)

# ---------- СТАТУСЫ ОДОБРЕНИЯ ----------
class ApprovalStatus(str, Enum):
    DRAFT = "draft"          # черновик
    PENDING = "pending"      # на рассмотрении
    APPROVED = "approved"    # одобрен
    REJECTED = "rejected"    # отклонен

class ApprovalInfo(BaseModel):
    is_approved: bool = False
    approval_status: ApprovalStatus = ApprovalStatus.DRAFT
    approval_requested_at: Optional[datetime] = None
    approval_requested_by: Optional[int] = None
    approval_handled_at: Optional[datetime] = None
    approval_handled_by: Optional[int] = None
    approval_comment: Optional[str] = None

class ApprovalAction(BaseModel):
    """Схема для принятия/отклонения заявки"""
    action: str = Field(..., description="approve или reject")
    comment: Optional[str] = Field(None, description="Комментарий к решению")

class ApprovalRequest(BaseModel):
    project_id: int
    project_title: str
    requested_by: int
    requested_by_name: str
    requested_at: datetime
    status: ApprovalStatus
    customer_name: Optional[str] = None
    
class ProjectApprovalList(BaseModel):
    """Список проектов для модерации"""
    pending: List[ApprovalRequest] = []
    approved: List[ApprovalRequest] = []
    rejected: List[ApprovalRequest] = []

# ---------- учитель ----------
class LifecycleStageState(BaseModel):
    id: str
    status: str = "pending"
    requested_by: Optional[int] = None
    requested_at: Optional[datetime] = None
    handled_by: Optional[int] = None
    handled_at: Optional[datetime] = None
    comment: Optional[str] = None


class ProjectLifecycleState(BaseModel):
    current_stage_id: Optional[str] = None
    stages: List[LifecycleStageState] = []


class LifecycleStageAction(BaseModel):
    comment: Optional[str] = None


class LifecycleStageDecision(BaseModel):
    action: str = Field(..., description="approve or reject")
    comment: Optional[str] = None


class EditingPresenceRequest(BaseModel):
    target_type: str = "task"
    target_id: str


class FileQuotaSettings(BaseModel):
    project_limit: int = 1024 * 1024 * 1024
    user_limit: int = 100 * 1024 * 1024


class ProjectQuotaOverride(BaseModel):
    project_limit: Optional[int] = None
    user_limit: Optional[int] = None


class TeacherRole(str, Enum):
    CUSTOMER = "customer"      # Заказчик
    EXPERT = "expert"           # Эксперт
    SUPERVISOR = "supervisor"   # Научный руководитель

class TeacherInfo(BaseModel):
    roles: List[TeacherRole] = Field(default=[], description="Роли учителя: заказчик, эксперт, научный руководитель")
    curator: bool = Field(default=False, description="Является ли куратором (отдельная роль)")

class TeacherBase(UserBase):
    is_teacher: bool = True
    teacher_info: TeacherInfo

class TeacherCreate(TeacherBase):
    password: str

class TeacherResponse(TeacherBase):
    id: int
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class TeacherUpdate(BaseModel):
    fullname: Optional[str] = None
    email: Optional[EmailStr] = None
    speciality: Optional[str] = None
    avatar: Optional[str] = None
    teacher_info: Optional[TeacherInfo] = None
    model_config = ConfigDict(populate_by_name=True)

# ---------- Общий пользователь ----------
class UserResponse(BaseModel):
    id: int
    nickname: str
    fullname: str
    email: EmailStr
    avatar: Optional[str] = None
    speciality: Optional[str] = None
    is_active: bool
    is_verified: bool
    is_teacher: bool
    class_: Optional[float] = Field(None, alias="class")
    teacher_info: Optional[TeacherInfo] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_admin: bool = False
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    google_id: Optional[str] = None
    vk_id: Optional[str] = None
    oauth_providers: List[str] = []

# ---------- Авторизация ----------
class LoginRequest(BaseModel):
    nickname: str
    password: str

# ---------- предложение ----------
class SuggestionStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"

class SuggestionCreate(BaseModel):
    target_type: str
    target_id: Optional[str] = None
    changes: Dict[str, Any]

class Suggestion(BaseModel):
    id: str
    author_id: int
    target_type: str  
    target_id: Optional[str] = None  
    changes: Dict[str, Any]        
    status: SuggestionStatus = SuggestionStatus.PENDING
    created_at: datetime
    comments: List[Comment] = []

# ---------- Проект ----------
class ProjectFileResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    uploaded_at: datetime
    uploaded_by: int
    task_id: Optional[int] = None
    required_file_id: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)
    is_old_vision: bool = False

class ProjectBase(BaseModel):
    ignore_file_limits: bool = False
    title: str = Field(..., min_length=1, json_schema_extra={"example": "Космическая программа"})
    class_key: Optional[str] = None
    direction_key: Optional[str] = None
    body: str = Field(..., min_length=1, json_schema_extra={"example": "Подробное описание..."})
    underbody: str = Field("", json_schema_extra={"example": "Дополнительные материалы"})
    participants: List[Participant] = Field(
        default=[],
        description="Список участников проекта с их ролями"
    )
    tasks: List[Dict[str, Any]] = Field(
        default=[],
        json_schema_extra={
            "example": [
                {"title": "расчёты", "status": "в процессе", "body": "очень важная задача", "timelinend": "20.11.2026", "timeline": "15.10.2025"},
                {"title": "разработка интерфейса", "status": "в работе", "body": "создать адаптивный дизайн", "timelinend": "01.12.2026", "timeline": "15.10.2025"},
                {"title": "тестирование", "status": "ожидает", "body": "проверить всё", "timelinend": "10.12.2026", "timeline": "15.10.2025"}
            ]
        }
    )
    links: Optional[Dict[str, str]] = Field(
        default=None,
        json_schema_extra={"example": {"github": "https://github.com/...", "google_drive": "https://drive.google.com/..."}}
    )
    comments: List[Comment] = Field(default=[], description="Комментарии к проекту")
    lifecycle_state: Optional[ProjectLifecycleState] = None
    file_quota_overrides: Dict[str, Any] = {}
    suggestions: List[Suggestion] = []
    is_old: bool = False
    required_roles: Optional[Dict[str, int]] = Field(
        default={},
        description="Целевое количество участников по ролям"
    )
    approval_info: Optional[ApprovalInfo] = None

class ProjectCreate(ProjectBase):
    pass  

class ProjectResponse(ProjectBase):
    suggestions: List[Suggestion] = []
    id: int
    is_hidden: bool = False
    hidden_by: Optional[int] = None
    hidden_by_users: Optional[Dict] = None
    join_requests: List[JoinRequest] = []
    hidden_by_users: List[int] = [] 
    model_config = ConfigDict(from_attributes=True)
    approval_info: Optional[ApprovalInfo] = None
    # Поля для версионирования
    current_version: Optional[int] = None
    current_points: Optional[int] = None
    points_to_next_checkpoint: Optional[int] = None

class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    class_key: Optional[str] = None
    direction_key: Optional[str] = None
    body: Optional[str] = None
    underbody: Optional[str] = None
    tasks: Optional[List[Dict[str, Any]]] = None
    participants: Optional[List[Participant]] = None
    is_old: Optional[bool] = None
    links: Optional[Dict[str, str]] = None
    comments: Optional[List[Comment]] = None
    lifecycle_state: Optional[ProjectLifecycleState] = None
    file_quota_overrides: Optional[Dict[str, Any]] = None
    ignore_file_limits: Optional[bool] = None
    required_roles: Optional[Dict[str, int]] = Field(
        default={},
        description="Целевое количество участников по ролям"
    )
    approval_info: Optional[ApprovalInfo] = None

# ---------- Email верификация ----------
class EmailVerificationCodeRequest(BaseModel):
    email: EmailStr

class EmailVerificationRequest(BaseModel):
    email: EmailStr
    code: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

# ---------- Токен схемы ----------
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

# ---------- приглашение ----------
class InvitationCreate(BaseModel):
    email: str
    role: ProjectRole

class InvitationInfo(BaseModel):
    token: str
    project_id: int
    project_title: str
    role: ProjectRole
    invited_by: int
    expires_at: datetime

class InvitationCreate(BaseModel):
    project_id: int
    invited_user_id: int
    role: ProjectRole

class InvitationResponse(BaseModel):
    id: int
    project_id: int
    project_title: Optional[str] = None
    invited_by: int
    invited_by_nickname: Optional[str] = None
    invited_user_id: int
    role: ProjectRole
    status: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class RequiredFile(BaseModel):
    name: str
    description: Optional[str] = ""

class TaskTemplate(BaseModel):
    title: str
    body: str
    status: str = "ожидает"
    timeline: str = ""
    timelinend: str = ""
    required_files: List[RequiredFile] = []

class ProjectCheckpointResponse(BaseModel):
    """Схема для отображения чекпоинта"""
    version: int
    created_at: Optional[datetime] = None
    created_by: Optional[int] = None
    created_by_name: Optional[str] = None
    message: str = ""
    total_points: int = 0
    changes_count: int = 0
    model_config = ConfigDict(from_attributes=True)


class ProjectChangeResponse(BaseModel):
    """Схема для отображения изменения"""
    version: str  # Например "1.3"
    checkpoint_version: int
    change_version: int
    change_type: str
    points: int
    description: str = ""
    created_at: Optional[datetime] = None
    created_by: Optional[int] = None
    created_by_name: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class ProjectVersionDetail(BaseModel):
    """Детальная информация о версии (чекпоинт + его изменения)"""
    version: str  # Например "1" или "1.3"
    is_current: bool = False
    created_at: Optional[datetime] = None
    created_by: Optional[int] = None
    message: str = ""
    total_points: int = 0
    points_to_next_checkpoint: Optional[int] = None  # Только для текущей версии
    changes: List[ProjectChangeResponse] = []


class ProjectVersionHistory(BaseModel):
    """Полная история версий проекта"""
    project_id: int
    points_threshold: int = 50
    checkpoints: List[ProjectVersionDetail] = []


class ProjectVersionStats(BaseModel):
    """Статистика версионирования проекта"""
    project_id: int
    total_checkpoints: int
    total_changes: int
    current_version: int
    current_points: int
    points_to_next_checkpoint: int
    points_threshold: int
    change_stats: Dict[str, int] = {}


class CreateCheckpointRequest(BaseModel):
    """Запрос на создание ручного чекпоинта"""
    message: str = Field("Manual checkpoint", description="Описание чекпоинта")


class CreateCheckpointResponse(BaseModel):
    """Ответ на создание чекпоинта"""
    message: str
    version: int
    total_points: int


class RestoreVersionResponse(BaseModel):
    """Ответ на восстановление версии"""
    message: str
    warning: str = "All changes after this version have been deleted"


class DeleteVersionResponse(BaseModel):
    """Ответ на удаление версии"""
    message: str
