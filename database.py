from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, JSON, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQL_DB_URL = 'sqlite:///./my_database.db'

engine = create_engine(SQL_DB_URL)

session_local = sessionmaker( autoflush=False, autocommit=False, bind=engine)


Base = declarative_base()

