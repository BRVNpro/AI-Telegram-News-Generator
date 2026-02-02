#!/bin/bash
set -e

echo "🚀 Starting services..."

# ---------- Redis ----------
if ! pgrep redis-server > /dev/null; then
  echo "🧠 Starting Redis..."
  redis-server --daemonize yes
else
  echo "🧠 Redis already running"
fi

# ---------- FastAPI ----------
if lsof -i :8000 > /dev/null; then
  echo "🌐 FastAPI already running on :8000"
else
  echo "🌐 Starting FastAPI..."
  uvicorn app.main:app --reload &
fi

sleep 2

# ---------- Celery worker ----------
if pgrep -f "celery worker" > /dev/null; then
  echo "⚙️ Celery worker already running"
else
  echo "⚙️ Starting Celery worker..."
  PYTHONPATH=. celery -A celery_worker.celery_app worker -l info &
fi

# ---------- Celery beat ----------
if pgrep -f "celery beat" > /dev/null; then
  echo "⏰ Celery beat already running"
else
  echo "⏰ Starting Celery beat..."
  PYTHONPATH=. celery -A celery_worker.celery_app beat -l info &
fi

echo "✅ All services started"
wait