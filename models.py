from sqlalchemy import Column, Integer, String, Float, JSON, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base
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

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
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
    
class ProjectFile(Base):
    __tablename__ = "project_files"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    task_id = Column(Integer, nullable=True)          # индекс задачи в массиве tasks (0‑based)
    filename = Column(String, nullable=False)         # уникальное имя файла на диске
    original_filename = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_deleted = Column(Boolean, default=False)
    compressed = Column(Boolean, default=False)