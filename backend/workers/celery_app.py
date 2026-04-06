from __future__ import annotations

from celery import Celery

from backend.config import settings

celery_app = Celery(
    "nexus",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "backend.workers.automation_trigger",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "backend.workers.automation_trigger.*": {"queue": "default"},
    },
)
