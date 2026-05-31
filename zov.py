from database import engine
from sqlalchemy import text

def migrate():
    with engine.connect() as conn:
        # ==================== USERS ====================
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
        
        # ==================== PROJECTS ====================
        result = conn.execute(text("PRAGMA table_info(projects)"))
        columns = [row[1] for row in result]
        
        if "required_roles" not in columns:
            conn.execute(text("ALTER TABLE projects ADD COLUMN required_roles JSON DEFAULT '{}'"))
            print("Added required_roles column")
        
        if "is_approved" not in columns:
            conn.execute(text("ALTER TABLE projects ADD COLUMN is_approved BOOLEAN DEFAULT FALSE"))
            print("Added is_approved column")
        
        if "approval_status" not in columns:
            conn.execute(text("ALTER TABLE projects ADD COLUMN approval_status VARCHAR DEFAULT 'draft'"))
            print("Added approval_status column")
        
        if "approval_requested_at" not in columns:
            conn.execute(text("ALTER TABLE projects ADD COLUMN approval_requested_at TIMESTAMP"))
            print("Added approval_requested_at column")
        
        if "approval_requested_by" not in columns:
            conn.execute(text("ALTER TABLE projects ADD COLUMN approval_requested_by INTEGER REFERENCES users(id)"))
            print("Added approval_requested_by column")
        
        if "approval_handled_at" not in columns:
            conn.execute(text("ALTER TABLE projects ADD COLUMN approval_handled_at TIMESTAMP"))
            print("Added approval_handled_at column")
        
        if "approval_handled_by" not in columns:
            conn.execute(text("ALTER TABLE projects ADD COLUMN approval_handled_by INTEGER REFERENCES users(id)"))
            print("Added approval_handled_by column")
        
        if "approval_comment" not in columns:
            conn.execute(text("ALTER TABLE projects ADD COLUMN approval_comment VARCHAR"))
            print("Added approval_comment column")
        
        # ==================== PROJECT_CHECKPOINTS ====================
        # Проверяем, существует ли таблица
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='project_checkpoints'"))
        if not result.fetchone():
            conn.execute(text("""
                CREATE TABLE project_checkpoints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL REFERENCES projects(id),
                    version INTEGER NOT NULL,
                    snapshot JSON NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER REFERENCES users(id),
                    message VARCHAR DEFAULT '',
                    total_points INTEGER DEFAULT 0
                )
            """))
            conn.execute(text("CREATE INDEX idx_checkpoint_project ON project_checkpoints(project_id)"))
            conn.execute(text("CREATE INDEX idx_checkpoint_version ON project_checkpoints(project_id, version)"))
            print("Created project_checkpoints table")
        else:
            # Проверяем колонки, если таблица уже есть
            result = conn.execute(text("PRAGMA table_info(project_checkpoints)"))
            cp_columns = [row[1] for row in result]
            
            if "message" not in cp_columns:
                conn.execute(text("ALTER TABLE project_checkpoints ADD COLUMN message VARCHAR DEFAULT ''"))
                print("Added message column to project_checkpoints")
            
            if "total_points" not in cp_columns:
                conn.execute(text("ALTER TABLE project_checkpoints ADD COLUMN total_points INTEGER DEFAULT 0"))
                print("Added total_points column to project_checkpoints")
        
        # ==================== PROJECT_CHANGES ====================
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='project_changes'"))
        if not result.fetchone():
            conn.execute(text("""
                CREATE TABLE project_changes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL REFERENCES projects(id),
                    checkpoint_version INTEGER NOT NULL,
                    change_version INTEGER NOT NULL,
                    change_type VARCHAR NOT NULL,
                    points INTEGER NOT NULL,
                    diff JSON NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER REFERENCES users(id),
                    description VARCHAR DEFAULT ''
                )
            """))
            conn.execute(text("CREATE INDEX idx_change_project ON project_changes(project_id)"))
            conn.execute(text("CREATE INDEX idx_change_version ON project_changes(project_id, checkpoint_version, change_version)"))
            print("Created project_changes table")
        else:
            # Проверяем колонки
            result = conn.execute(text("PRAGMA table_info(project_changes)"))
            pc_columns = [row[1] for row in result]
            
            if "description" not in pc_columns:
                conn.execute(text("ALTER TABLE project_changes ADD COLUMN description VARCHAR DEFAULT ''"))
                print("Added description column to project_changes")
        
        conn.commit()
        print("Migration completed successfully!")

if __name__ == "__main__":
    migrate()