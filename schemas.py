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

# ---------- учитель ----------
class TeacherRole(str, Enum):
    CUSTOMER = "customer"      # Заказчик
    EXPERT = "expert"           # Эксперт
    SUPERVISOR = "supervisor"   # Научный руководитель
    #куратор будет отдельно

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

# ---------- Авторизация ----------
class LoginRequest(BaseModel):
    nickname: str
    password: str
# ---------- предложение ----------
class SuggestionStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"



# Схема для создания предложения 
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
    filename: str               # оригинальное имя
    original_filename: str
    file_size: int
    mime_type: str
    uploaded_at: datetime
    uploaded_by: int
    task_id: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)
class ProjectBase(BaseModel):
    title: str = Field(..., min_length=1, json_schema_extra={"example": "Космическая программа"})
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
    suggestions: List[Suggestion] = []
    is_old: bool = False

class ProjectCreate(ProjectBase):
    pass  

class ProjectResponse(ProjectBase):
    suggestions: List[Suggestion] = []
    id: int
    is_hidden: bool = False
    hidden_by: Optional[int] = None
    hidden_by_users : Optional[Dict] = None
    join_requests: List[JoinRequest] = []
    hidden_by_users: List[int] = [] 
    model_config = ConfigDict(from_attributes=True)

class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    underbody: Optional[str] = None
    tasks: Optional[List[Dict[str, Any]]] = None
    participants: Optional[List[Participant]] = None
    is_old: Optional[bool] = None
    links: Optional[Dict[str, str]] = None
    comments: Optional[List[Comment]] = None

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
    
class JoinRequest(BaseModel):
    id: str
    user_id: int
    created_at: datetime
    status: str  