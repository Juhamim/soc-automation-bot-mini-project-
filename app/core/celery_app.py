from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "soc_bot",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.core.tasks"],
)

celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # Timezone
    timezone="UTC",
    enable_utc=True,

    # Task behavior
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,

    # Result expiry (24h)
    result_expires=86400,

    # Retry policy
    task_max_retries=3,
    task_default_retry_delay=5,

    # Routes
    task_routes={
        "app.core.tasks.process_alert": {"queue": "alerts"},
        "app.core.tasks.generate_and_send_report": {"queue": "celery"},
        "app.core.tasks.run_aggregation": {"queue": "celery"},
    },

    # Scheduled Tasks
    beat_schedule={
        "daily-soc-report": {
            "task": "app.core.tasks.generate_and_send_report",
            "schedule": crontab(hour=17, minute=0),  # Run daily at 17:00 UTC
            "kwargs": {"timeframe": "Daily", "hours": 24},
        },
        "aggregate-incidents-every-15-mins": {
            "task": "app.core.tasks.run_aggregation",
            "schedule": crontab(minute="*/15"),
        }
    }
)
