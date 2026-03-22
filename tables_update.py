# upgrade_table.py
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv
import os

load_dotenv()

# Подключение к базе данных
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./my_database.db")

def upgrade_users_table():
    """
    Добавляет новые поля в существующую таблицу users
    без потери данных
    """
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # Начинаем транзакцию
            trans = conn.begin()
            
            try:
                print("🔄 Проверяем и добавляем новые поля...")
                
                # Проверяем и добавляем поле is_teacher
                try:
                    conn.execute(text("ALTER TABLE users ADD COLUMN is_teacher BOOLEAN DEFAULT FALSE"))
                    print("   ✅ Добавлено поле is_teacher")
                except Exception as e:
                    if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                        print("   ℹ️ Поле is_teacher уже существует")
                    else:
                        print(f"   ⚠️ Ошибка при добавлении is_teacher: {e}")
                
                # Проверяем и добавляем поле teacher_info
                try:
                    conn.execute(text("ALTER TABLE users ADD COLUMN teacher_info JSON"))
                    print("   ✅ Добавлено поле teacher_info")
                except Exception as e:
                    if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                        print("   ℹ️ Поле teacher_info уже существует")
                    else:
                        print(f"   ⚠️ Ошибка при добавлении teacher_info: {e}")
                
                # Подтверждаем транзакцию
                trans.commit()
                print("\n✅ Апгрейд таблицы users завершен!")
                
            except Exception as e:
                trans.rollback()
                print(f"❌ Ошибка при выполнении операции: {e}")
                raise
                
    except SQLAlchemyError as e:
        print(f"❌ Ошибка подключения к базе данных: {e}")

def check_current_structure():
    """
    Проверяет текущую структуру таблицы
    """
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            print("\n📊 ТЕКУЩАЯ СТРУКТУРА ТАБЛИЦЫ users:")
            print("=" * 70)
            
            # Для SQLite
            result = conn.execute(text("PRAGMA table_info(users)"))
            columns = result.fetchall()
            
            print(f"{'Колонка':<20} {'Тип':<15} {'Null':<8} {'По умолчанию'}")
            print("-" * 70)
            
            has_is_teacher = False
            has_teacher_info = False
            
            for col in columns:
                name, type_, notnull, dflt_value, pk = col[1], col[2], col[3], col[4], col[5]
                null_str = "NO" if notnull else "YES"
                print(f"{name:<20} {type_:<15} {null_str:<8} {dflt_value or ''}")
                
                if name == 'is_teacher':
                    has_is_teacher = True
                if name == 'teacher_info':
                    has_teacher_info = True
            
            print("-" * 70)
            print(f"\n🔍 Статус новых полей:")
            print(f"   is_teacher: {'✅' if has_is_teacher else '❌'} присутствует")
            print(f"   teacher_info: {'✅' if has_teacher_info else '❌'} присутствует")
            
    except Exception as e:
        print(f"❌ Ошибка при проверке структуры: {e}")

def fix_existing_teachers():
    """
    Опционально: обновляет существующих учителей
    (если у вас уже были учителя в старой структуре)
    """
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            trans = conn.begin()
            
            try:
                print("\n🔄 Обновляем существующих учителей...")
                
                # Находим пользователей, которые могут быть учителями
                # (например, по наличию prof в старых данных)
                result = conn.execute(text("""
                    SELECT id, nickname, speciality 
                    FROM users 
                    WHERE speciality LIKE '%учитель%' 
                       OR speciality LIKE '%преподаватель%'
                       OR is_teacher IS NULL
                """))
                
                teachers = result.fetchall()
                
                if teachers:
                    for teacher in teachers:
                        # Помечаем как учителя
                        conn.execute(
                            text("UPDATE users SET is_teacher = TRUE WHERE id = :id"),
                            {"id": teacher[0]}
                        )
                        print(f"   ✅ Обновлен пользователь ID {teacher[0]}: {teacher[1]} -> is_teacher = TRUE")
                    
                    print(f"\n✅ Обновлено учителей: {len(teachers)}")
                else:
                    print("   ℹ️ Учителей для обновления не найдено")
                
                trans.commit()
                
            except Exception as e:
                trans.rollback()
                print(f"❌ Ошибка при обновлении учителей: {e}")
                
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("🔄 АПГРЕЙД ТАБЛИЦЫ users")
    print("=" * 60)
    
    # Проверяем текущую структуру
    check_current_structure()
    
    print("\n" + "=" * 60)
    print("Действия:")
    print("1. Добавить новые поля (is_teacher, teacher_info)")
    print("2. Добавить поля и обновить существующих учителей")
    print("3. Только проверить структуру")
    print("4. Выйти")
    
    choice = input("\nВыберите действие (1-4): ").strip()
    
    if choice == "1":
        upgrade_users_table()
        check_current_structure()
    elif choice == "2":
        upgrade_users_table()
        fix_existing_teachers()
        check_current_structure()
    elif choice == "3":
        check_current_structure()
    elif choice == "4":
        print("👋 Выход...")
    else:
        print("❌ Неверный выбор")