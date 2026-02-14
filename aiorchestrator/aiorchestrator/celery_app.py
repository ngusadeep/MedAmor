"""Celery app configuration for async task processing."""

import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

# Redis connection URL
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

# Create Celery app
celery_app = Celery(
    "medaudit_orchestrator",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["aiorchestrator.tasks"],  # Auto-discover tasks
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Task results expire after 1 hour
    result_expires=3600,
    # Max tasks per worker before restart (prevent memory leaks)
    worker_max_tasks_per_child=100,
    # Task timeout: 5 minutes max per audit
    task_time_limit=300,
    task_soft_time_limit=240,
    # Retry configuration
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)
