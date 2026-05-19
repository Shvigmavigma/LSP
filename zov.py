from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, JSON, text
SQL_DB_URL = 'sqlite:///./my_database.db'
engine = create_engine(SQL_DB_URL)
with engine.connect() as conn:
    conn.execute(text("ALTER TABLE projects ADD COLUMN required_roles JSON DEFAULT '{}'"))
    conn.commit()