from sqlalchemy import Column, Integer, String, Float, JSON, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
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
    
    # Поля для email-авторизации
    is_active = Column(Boolean, default=False)      # Активен ли пользователь
    is_verified = Column(Boolean, default=False)    # Подтвержден ли email
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
    participants = Column(JSON, default=list)          # список словарей Participant
    tasks = Column(JSON, default=list)
    links = Column(JSON, default=dict)
    comments = Column(JSON, default=list)
    suggestions = Column(JSON, default=list)           # <-- новое поле для предложений
    join_requests = Column(JSON, default=list)