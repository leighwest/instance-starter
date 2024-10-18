import os
from celery import Celery
from celery.signals import setup_logging  # noqa

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "instance_starter.settings")
app = Celery("instance_starter")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks(['instance_starter.ec2_starter'])


