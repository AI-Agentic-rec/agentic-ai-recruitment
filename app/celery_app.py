from celery import Celery

from app.config import get_settings


settings = get_settings()
celery_app = Celery(
    "recruitment",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]


@celery_app.task
def health_check_task() -> str:
    return "ok"
