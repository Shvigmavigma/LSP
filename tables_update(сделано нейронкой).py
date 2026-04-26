"""
Миграция: добавление столбца ignore_file_limits в таблицу projects
Запустить один раз: python migrate_add_ignore_file_limits.py
"""

import os
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./my_database.db")

def run_migration():
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('projects')]

    if 'ignore_file_limits' in columns:
        print("✅ Столбец 'ignore_file_limits' уже существует. Миграция не требуется.")
        return

    # Универсальный BOOLEAN DEFAULT FALSE
    alter_query = "ALTER TABLE projects ADD COLUMN ignore_file_limits BOOLEAN DEFAULT FALSE;"

    with engine.connect() as conn:
        trans = conn.begin()
        try:
            conn.execute(text(alter_query))
            trans.commit()
            print("✅ Столбец 'ignore_file_limits' успешно добавлен в таблицу projects.")
        except Exception as e:
            trans.rollback()
            print(f"❌ Ошибка при выполнении миграции: {e}")
            raise

if __name__ == "__main__":
    print(f"Текущая директория: {os.getcwd()}")
    run_migration()