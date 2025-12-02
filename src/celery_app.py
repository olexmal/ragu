"""
Celery Application Configuration
Background job queue for long-running tasks like web scraping.
"""
import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

# Redis broker URL
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Create Celery app
celery_app = Celery(
    'ragu',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['src.tasks']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task (default)
    task_soft_time_limit=3300,  # 55 minutes soft limit (default)
    worker_prefetch_multiplier=1,  # Process one task at a time per worker
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks to prevent memory leaks
)

# Task-specific time limits (override defaults for long-running tasks)
# Use task_annotations for time limits, not task_routes
celery_app.conf.task_annotations = {
    'src.tasks.scrape_and_embed_url': {
        'time_limit': 14400,  # 4 hours for web scraping (can process many pages)
        'soft_time_limit': 13800,  # 3h 50min soft limit
    }
}

# Task routing - removed to use default 'celery' queue
# If you want to use a separate queue, make sure workers listen to it with -Q celery,scraping
# celery_app.conf.task_routes = {
#     'src.tasks.scrape_and_embed_url': {'queue': 'scraping'},
# }

