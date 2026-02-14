#!/bin/bash
set -e

echo "Starting Platform..."

# Wait for database to be ready
echo "Waiting for database..."
while ! nc -z ${DATABASE_HOST:-platform_db} ${DATABASE_PORT:-5432}; do
    sleep 1
done
echo "Database is ready!"

# Run migrations (idempotent: only pending migrations run)
echo "Running database migrations..."
cd /app
uv run alembic upgrade head

# Ensure default admin user exists (skips if user already exists or env not set)
echo "Ensuring default admin user..."
uv run python -m backend.startup

# Start Flask backend with hot reload in development
echo "Starting Flask backend..."
if [ "$FLASK_ENV" = "development" ]; then
    uv run python -m backend.app &
else
    uv run gunicorn -w 4 -b 127.0.0.1:5000 backend.app:app &
fi

# Start frontend in development mode
if [ "$FLASK_ENV" = "development" ]; then
    echo "Starting Vite dev server..."
    cd /app/ui
    npm run dev &
fi

# Start nginx
echo "Starting nginx..."
if [ "$FLASK_ENV" = "development" ]; then
    nginx -c /app/nginx.conf -g 'daemon off;'
else
    nginx -c /app/nginx.prod.conf -g 'daemon off;'
fi
