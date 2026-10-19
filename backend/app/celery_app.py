from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "cv_ai_matcher",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]

celery_app.conf.imports = [
    "app.services.cv_pipeline.tasks",
    "app.services.cv_pipeline.recovery",
    "app.services.job_pipline.tasks",
]

celery_app.conf.broker_transport_options = {"visibility_timeout": 120}

celery_app.conf.beat_schedule = {
    "recover-stale-pending-cv": {
        "task": "cv_pipeline.recover_stale_pending",
        "schedule": settings.STALE_PENDING_CHECK_INTERVAL_SECONDS,
    },
}
