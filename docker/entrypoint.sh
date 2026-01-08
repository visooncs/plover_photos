#!/bin/sh

# Wait for database connection if needed (simple sleep or loop)
# echo "Waiting for database..."
# sleep 5

echo "Apply database migrations"
python manage.py migrate

echo "Collect static files"
python manage.py collectstatic --noinput

echo "Starting server"
# 进一步增加超时时间到 1000 秒，以防 AI 任务执行时间过长
# 使用 --graceful-timeout 允许平滑退出
exec gunicorn core.wsgi:application --bind 0.0.0.0:8000 --timeout 1000 --graceful-timeout 300 --workers 1 --worker-class sync
