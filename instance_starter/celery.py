import os
from celery import Celery
from celery.signals import setup_logging  # noqa

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "instance_starter.settings")
app = Celery("instance_starter")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks(['ec2_starter'])

app.conf.beat_schedule = {
    'broadcast-ec2-instance-statuses': {
        'task': 'ec2_starter.service.ec2_service.broadcast_ec2_instance_statuses',
        'schedule': 10.0,
    },
}