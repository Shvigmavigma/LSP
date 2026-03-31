# add_required_file_id_column.py
import os
import sqlite3
from sqlalchemy import create_engine, MetaData, Table, Column, String
from sqlalchemy.orm import sessionmaker
from database import engine, session_local
from models import ProjectFile

def add_required_file_id_column():
    """Добавляет колонку required_file_id в таблицу project_files, если её нет."""
    inspector = inspect(engine)
    if 'required_file_id' not in [c['name'] for c in inspector.get_columns('project_files')]:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE project_files ADD COLUMN required_file_id VARCHAR"))
            conn.commit()
        print("Колонка required_file_id добавлена.")
    else:
        print("Колонка required_file_id уже существует.")

if __name__ == "__main__":
    from sqlalchemy import inspect, text
    add_required_file_id_column()