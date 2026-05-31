from sqlalchemy import Column, Integer, String, Float, JSON, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    nickname = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)        
    fullname = Column(String, nullable=False, index=True)
    class_ = Column(Float, default=0.0)
    speciality = Column(String, nullable=True)
    email = Column(String, nullable=False, index=True, unique=True)
    avatar = Column(String, nullable=True)
    

    is_active = Column(Boolean, default=False)    
    is_verified = Column(Boolean, default=False)   
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_teacher = Column(Boolean, default=False, nullable=False) 
    teacher_info = Column(JSON, nullable=True)
    is_admin = Column(Boolean, default=False, nullable=False)
    google_id = Column(String, nullable=True, unique=True)
    vk_id = Column(String, nullable=True, unique=True)
    oauth_providers = Column(JSON, default=list)  # ['google', 'vk']

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    ignore_file_limits = Column(Boolean, default=False)
    title = Column(String, nullable=False, index=True)
    body = Column(String, nullable=False)
    underbody = Column(String, default="")
    participants = Column(JSON, default=list)        
    tasks = Column(JSON, default=list)
    links = Column(JSON, default=dict)
    comments = Column(JSON, default=list)
    suggestions = Column(JSON, default=list)          
    join_requests = Column(JSON, default=list)
    is_hidden = Column(Boolean, default=False)
    hidden_by = Column(Integer, nullable=True)
    hidden_by_users = Column(JSON, default=list)
    is_old = Column(Boolean, default=False)
    required_roles = Column(JSON, default={})
    invitations = relationship("Invitation", back_populates="project", cascade="all, delete-orphan")
    is_approved = Column(Boolean, default=False)  # одобрен ли проект
    approval_status = Column(String, default="draft")  # draft, pending, approved, rejected
    approval_requested_at = Column(DateTime, nullable=True)  # когда отправлена заявка
    approval_requested_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # кто отправил заявку
    approval_handled_at = Column(DateTime, nullable=True)  # когда обработана заявка
    approval_handled_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # кто обработал заявку
    approval_comment = Column(String, nullable=True)  # комментарий к решению
class ProjectFile(Base):
    __tablename__ = "project_files"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    task_id = Column(Integer, nullable=True)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_deleted = Column(Boolean, default=False)
    compressed = Column(Boolean, default=False)
    required_file_id = Column(String, nullable=True)
    is_old_vision = Column(Boolean, default=False)

class Invitation(Base):
    __tablename__ = "invitations"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    invited_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    invited_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String, nullable=False)  # ProjectRole value
    status = Column(String, default="pending")  # pending, accepted, rejected, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    project = relationship("Project", back_populates="invitations")
    inviter = relationship("User", foreign_keys=[invited_by])
    invitee = relationship("User", foreign_keys=[invited_user_id])
    
# models.py - добавить в конец файла

class ProjectCheckpoint(Base):
    __tablename__ = "project_checkpoints"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    version = Column(Integer, nullable=False)  # 1, 2, 3...
    snapshot = Column(JSON, nullable=False)  # Полный снимок проекта
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    message = Column(String, default="")  # Описание чекпоинта
    total_points = Column(Integer, default=0)  # Сумма очков до этого чекпоинта


class ProjectChange(Base):
    __tablename__ = "project_changes"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    checkpoint_version = Column(Integer, nullable=False)  # На каком чекпоинте основано
    change_version = Column(Integer, nullable=False)  # Порядковый номер изменения (1, 2, 3...)
    change_type = Column(String, nullable=False)  # Тип изменения
    points = Column(Integer, nullable=False)  # 1, 3, 5, 10
    diff = Column(JSON, nullable=False)  # Только изменённые поля
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    description = Column(String, default="")  # Автоматическое описание