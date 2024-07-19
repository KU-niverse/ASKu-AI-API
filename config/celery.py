import os
from celery import Celery
from celery.schedules import crontab


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
app = Celery('config')
app.config_from_object(
    "django.conf:settings",
    namespace="CELERY",
)
app.autodiscover_tasks()
app.conf.timezone = 'Asia/Seoul'

app.conf.beat_schedule = {
    "weekly-wiki-data-update": {
        "task": "chatbot.tasks.wiki_data_schedule",
        "schedule": crontab(
            minute=0,
            hour=3,
            day_of_week='monday'
        )
    }
}
