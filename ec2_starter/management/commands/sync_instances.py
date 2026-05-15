import logging
import boto3
from django.core.management.base import BaseCommand
from django.conf import settings
from ec2_starter.models import EC2

logger = logging.getLogger('instance_starter')

DISCOVERY_TAG = 'instance-starter-toy'

class Command(BaseCommand):
    help = 'Sync EC2 instances tagged Role=instance-starter-toy into the database'

    def handle(self, *args, **options):
        ec2 = boto3.client(
            'ec2',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )

        response = ec2.describe_instances(
            Filters=[{'Name': 'tag:Role', 'Values': [DISCOVERY_TAG]}]
        )

        instances = [
            i
            for r in response['Reservations']
            for i in r['Instances']
        ]

        if not instances:
            self.stdout.write(self.style.WARNING('No instances found with Role={DISCOVERY_TAG}'))
            return

        for instance in instances:
            tags = {t['Key']: t['Value'] for t in instance.get('Tags', [])}
            instance_id = instance['InstanceId']
            name = tags.get('Name', instance_id)

            obj, created = EC2.objects.update_or_create(
                instance_id=instance_id,
                defaults={
                    'name': name,
                    'region': settings.AWS_REGION,
                }
            )

            action = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(f'{action}: {name} ({instance_id})'))