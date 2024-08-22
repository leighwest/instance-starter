from django.db import models


class Ec2(models.Model):
    instance_id = models.CharField(max_length=20, unique=True)
    region = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    state = models.CharField(max_length=20)
    last_start_time = models.DateTimeField(null=True, blank=True)