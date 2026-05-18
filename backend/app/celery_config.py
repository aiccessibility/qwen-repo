"""
Celery configuration for accessibility audit tasks.
"""
from celery import Celery
from app.utils.config import settings

# Create Celery app
celery_app = Celery(
    'accessibility',
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=['app.tasks.audit_tasks']
)

# Celery configuration
celery_app.conf.update(
    # Task serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # Timezone
    timezone='UTC',
    enable_utc=True,
    
    # Task execution settings
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    task_soft_time_limit=3300,  # 55 minutes soft limit
    
    # Result backend settings
    result_expires=86400,  # Results expire after 24 hours
    result_extended=True,  # Store additional task metadata
    
    # Rate limiting
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    
    # Retry settings
    task_default_retry_delay=300,  # 5 minutes between retries
    task_max_retries=3,
    
    # Event monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
)

# Auto-discover tasks from tasks module
celery_app.autodiscover_tasks(['app'])
