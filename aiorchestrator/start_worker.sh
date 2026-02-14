#!/bin/bash
# Start Celery worker for processing audit jobs

echo "Starting Celery Worker for MedAudit..."
echo "========================================"

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check if Redis is running (try redis-cli if available, otherwise skip check)
if command -v redis-cli &> /dev/null; then
    if redis-cli ping > /dev/null 2>&1; then
        echo "✓ Redis is running"
    else
        echo "⚠ Warning: redis-cli found but cannot connect to Redis"
        echo "  Make sure Redis is running: docker compose up redis -d"
    fi
else
    echo "ℹ Skipping Redis check (redis-cli not installed)"
    echo "  Ensure Redis is running: docker compose up redis -d"
fi
echo ""
echo "Starting worker with concurrency=2..."
echo "Press Ctrl+C to stop"
echo ""

# Start Celery worker
# Use --pool=solo on macOS to avoid fork issues
uv run celery -A aiorchestrator.celery_app worker \
    --pool=solo \
    --loglevel=info
