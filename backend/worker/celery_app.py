from __future__ import annotations

import os

from celery import Celery


def _make_celery() -> Celery:
    broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    result_backend = os.getenv("CELERY_RESULT_BACKEND", broker_url)
    celery = Celery(
        "quell_ai_ingest",
        broker=broker_url,
        backend=result_backend,
        include=["worker.tasks"],
    )
    celery.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        task_track_started=True,
        worker_send_task_events=True,
    )
    return celery


celery_app = _make_celery()

