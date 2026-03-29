import sqlite3
conn = sqlite3.connect("my_database.db")
conn.execute("ALTER TABLE project_files ADD COLUMN compressed BOOLEAN DEFAULT 0")
conn.commit()
conn.close()