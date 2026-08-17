import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

SQL_DB_URL = os.getenv("DATABASE_URL", "sqlite:///./my_database.db")

engine_kwargs = {"pool_pre_ping": True}
if SQL_DB_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(SQL_DB_URL, **engine_kwargs)

session_local = sessionmaker(autoflush=False, autocommit=False, bind=engine)

Base = declarative_base()

