import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

app = Celery("backend")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Explicitly import task modules that are not under INSTALLED_APPS packages
# so the worker registers them (beat enqueues by string name).
# NOTE: Companies/Jobs/News tasks moved to data-ingestion-system (FastAPI + APScheduler)
app.conf.imports = app.conf.imports + (
    "DataIngestion.Gmail.tasks",
    "DataIngestion.GoogleCalendar.tasks",
    "Intelligence.vectorDB.tasks",
)


@app.task(bind=True)
def debug_task(self):  # pragma: no cover
    print(f"Request: {self.request!r}")
