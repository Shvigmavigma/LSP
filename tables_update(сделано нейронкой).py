"""
Миграция: добавление столбца required_file_id в таблицу project_files
Запустить один раз: python migrate_add_required_file_id.py
"""

import sqlite3
import os
from pathlib import Path
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

load_dotenv()

# Настройка подключения – замените на ваш URL базы данных, если он отличается
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./my_database.db")

def run_migration():
    engine = create_engine(DATABASE_URL)
    
    # Проверяем, есть ли уже столбец required_file_id
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('project_files')]
    
    if 'required_file_id' in columns:
        print("✅ Столбец 'required_file_id' уже существует. Миграция не требуется.")
        return
    
    # Определяем тип столбца в зависимости от диалекта
    if engine.dialect.name == 'sqlite':
        alter_query = "ALTER TABLE project_files ADD COLUMN required_file_id VARCHAR;"
    elif engine.dialect.name == 'postgresql':
        alter_query = "ALTER TABLE project_files ADD COLUMN required_file_id VARCHAR;"
    elif engine.dialect.name == 'mysql':
        alter_query = "ALTER TABLE project_files ADD COLUMN required_file_id VARCHAR(255);"
    else:
        # Для других СУБД используем универсальный синтаксис
        alter_query = "ALTER TABLE project_files ADD COLUMN required_file_id VARCHAR(255);"
    
    with engine.connect() as conn:
        # Начинаем транзакцию (для поддержки отката в случае ошибки)
        trans = conn.begin()
        try:
            conn.execute(text(alter_query))
            trans.commit()
            print("✅ Столбец 'required_file_id' успешно добавлен в таблицу project_files.")
        except Exception as e:
            trans.rollback()
            print(f"❌ Ошибка при выполнении миграции: {e}")
            raise

if __name__ == "__main__":
    # Убедимся, что мы в правильной директории
    print(f"Текущая директория: {os.getcwd()}")
    run_migration()