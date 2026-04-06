from __future__ import annotations

from typing import Any


async def fire_trigger(automation_id: str, event: str, payload: dict[str, Any] | None = None) -> None:
    """Dispatch an automation trigger event to the task queue (stub)."""
    try:
        from backend.workers.celery_app import celery_app
        celery_app.send_task(
            "backend.workers.automation_trigger.run_automation",
            args=[automation_id, event, payload or {}],
            queue="default",
        )
    except Exception:
        pass
