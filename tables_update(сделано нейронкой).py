import sqlite3
import os

DB_PATH = "my_database.db"  # путь к вашей базе данных

def create_project_files_table():
    if not os.path.exists(DB_PATH):
        print(f"База данных {DB_PATH} не найдена!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Проверяем, существует ли таблица
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='project_files'")
    if cursor.fetchone():
        print("Таблица project_files уже существует.")
        conn.close()
        return

    # Создаём таблицу
    cursor.execute('''
        CREATE TABLE project_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            task_id INTEGER,
            filename TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            mime_type TEXT NOT NULL,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            uploaded_by INTEGER NOT NULL,
            is_deleted BOOLEAN DEFAULT 0,
            FOREIGN KEY(project_id) REFERENCES projects(id),
            FOREIGN KEY(uploaded_by) REFERENCES users(id)
        )
    ''')

    # Создаём индексы для ускорения запросов
    cursor.execute("CREATE INDEX idx_project_files_project ON project_files(project_id)")
    cursor.execute("CREATE INDEX idx_project_files_task ON project_files(task_id)")
    cursor.execute("CREATE INDEX idx_project_files_uploaded_by ON project_files(uploaded_by)")

    conn.commit()
    conn.close()
    print("Таблица project_files успешно создана.")

if __name__ == "__main__":
    create_project_files_table()