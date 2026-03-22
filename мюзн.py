import sqlite3
import os

DB_PATH = "my_database.db"

def add_is_admin_column():
    if not os.path.exists(DB_PATH):
        print(f"Ошибка: файл базы данных {DB_PATH} не найден.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]

        if "is_admin" not in columns:
            print("Добавление колонки is_admin в таблицу users...")
            cursor.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0")
            conn.commit()
            print("✅ Колонка is_admin успешно добавлена.")
        else:
            print("ℹ️ Колонка is_admin уже существует.")
    except sqlite3.Error as e:
        print(f"❌ Ошибка SQLite: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    add_is_admin_column()