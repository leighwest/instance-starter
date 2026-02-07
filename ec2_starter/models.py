from django.db import models

class EC2(models.Model):
    instance_id = models.CharField(max_length=20, unique=True)
    region = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    description = models.TextField(max_length=500, blank=True)

    class DoesNotExist(Exception):
        pass

    @classmethod
    def get_by_name(cls, name):
        try:
            return cls.objects.get(name=name)
        except cls.DoesNotExist:
            return None
        except cls.MultipleObjectsReturned:
            return cls.objects.filter(name=name).first()
