import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djing.settings")
app = Celery('djing', broker='redis://localhost:6379/0')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()
