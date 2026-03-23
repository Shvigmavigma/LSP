import sqlite3
import os

DB_PATH = "my_database.db"

def update_hidden_by_users_to_empty():
    if not os.path.exists(DB_PATH):
        print("БД не найдена")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Проверяем существование колонки
        cursor.execute("PRAGMA table_info(projects)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "hidden_by_users" not in columns:
            print("Колонка hidden_by_users не существует")
            return
        
        # Обновляем все записи, устанавливая значение '[]'
        cursor.execute("UPDATE projects SET hidden_by_users = '[]'")
        conn.commit()
        
        # Проверяем, сколько строк обновлено
        print(f"Все записи обновлены. Значение hidden_by_users установлено как '[]' для всех строк")
        
        # Дополнительно: показываем пример обновленных данных
        cursor.execute("SELECT id, hidden_by_users FROM projects LIMIT 5")
        rows = cursor.fetchall()
        if rows:
            print("\nПример обновленных данных (первые 5 записей):")
            for row in rows:
                print(f"  ID: {row[0]}, hidden_by_users: {row[1]}")
        
    except sqlite3.Error as e:
        print(f"Ошибка SQLite: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    update_hidden_by_users_to_empty()