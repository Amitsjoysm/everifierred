from celery import Celery
from config import settings
import logging

logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    'email_verifier',
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=['tasks']
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)

logger.info("Celery app configured successfully")
