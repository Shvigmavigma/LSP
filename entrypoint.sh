#!/bin/sh
set -e

python - <<'PY'
import os
import time

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise SystemExit(0)

engine = create_engine(database_url, pool_pre_ping=True)
for attempt in range(1, 31):
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        print("Database is ready")
        break
    except OperationalError as exc:
        if attempt == 30:
            raise
        print(f"Waiting for database ({attempt}/30): {exc}")
        time.sleep(2)
PY

exec uvicorn main:app --host 0.0.0.0 --port 8000
