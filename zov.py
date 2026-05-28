from database import engine
from sqlalchemy import text

def migrate():
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(users)"))
        columns = [row[1] for row in result]
        
        if "google_id" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN google_id VARCHAR"))
            print("Added google_id column")
        
        if "vk_id" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN vk_id VARCHAR"))
            print("Added vk_id column")
        
        if "oauth_providers" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN oauth_providers JSON DEFAULT '[]'"))
            print("Added oauth_providers column")
        
        conn.commit()
        print("Migration completed")

if __name__ == "__main__":
    migrate()