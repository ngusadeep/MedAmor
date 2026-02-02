"""Celery app: broker RabbitMQ, task queue for audit jobs."""

from celery import Celery

from app.core.config import settings

# Result backend: use rpc:// with RabbitMQ (amqp result backend was removed in Celery 5).
celery_app = Celery(
    "medaudit",
    broker=settings.celery_broker_url,
    backend=getattr(settings, "celery_result_backend", None) or "rpc://",
    include=["app.worker.tasks"],
)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)
