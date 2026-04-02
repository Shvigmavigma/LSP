# migrate_add_is_old.py
import os
from sqlalchemy import create_engine, inspect, text
from dotenv import load_dotenv
from models import Base, Project  # импорт вашей модели Project

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./my_database.db")
engine = create_engine(DATABASE_URL)

def add_is_old_column():
    # Создаём все таблицы, если их нет (чтобы models были зарегистрированы)
    Base.metadata.create_all(engine)
    
    inspector = inspect(engine)
    if 'projects' not in inspector.get_table_names():
        print("Таблица 'projects' не найдена и не была создана")
        return
    
    columns = [col['name'] for col in inspector.get_columns('projects')]
    if 'is_old' in columns:
        print("Колонка 'is_old' уже существует")
        return
    
    with engine.connect() as conn:
        # Для SQLite
        if engine.dialect.name == 'sqlite':
            conn.execute(text("ALTER TABLE projects ADD COLUMN is_old BOOLEAN NOT NULL DEFAULT 0"))
        elif engine.dialect.name == 'postgresql':
            conn.execute(text("ALTER TABLE projects ADD COLUMN is_old BOOLEAN NOT NULL DEFAULT false"))
        elif engine.dialect.name == 'mysql':
            conn.execute(text("ALTER TABLE projects ADD COLUMN is_old BOOLEAN NOT NULL DEFAULT FALSE"))
        else:
            conn.execute(text("ALTER TABLE projects ADD COLUMN is_old BOOLEAN DEFAULT 0"))
        conn.commit()
    
    print("Колонка 'is_old' успешно добавлена")

if __name__ == "__main__":
    add_is_old_column()