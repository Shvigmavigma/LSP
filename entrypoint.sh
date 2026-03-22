#!/bin/bash

# Запускаем миграции базы данных, если они есть (опционально)
# alembic upgrade head

# Запускаем сервер
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000