#!/bin/bash
# Start Celery worker for processing audit jobs

echo "Starting Celery Worker for MedAudit..."
echo "========================================"

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "⚠ Redis is not running!"
    echo ""
    echo "Start it with:"
    echo "  docker compose up redis -d"
    echo ""
    echo "Or install locally:"
    echo "  Mac: brew install redis && redis-server"
    echo "  Linux: sudo apt install redis-server && redis-server"
    exit 1
fi

echo "✓ Redis is running"
echo ""
echo "Starting worker with concurrency=2..."
echo "Press Ctrl+C to stop"
echo ""

# Start Celery worker
# Use --pool=solo on macOS to avoid fork issues
uv run celery -A aiorchestrator.celery_app worker \
    --pool=solo \
    --loglevel=info
