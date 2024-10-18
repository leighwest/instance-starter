import boto3
import pytz
from datetime import datetime, timedelta

from celery import shared_task
from django.conf import settings
from botocore.exceptions import ClientError

import logging

logger = logging.getLogger('instance_starter')
logger.propagate = True

def get_ec2_instance_status(instance_id):
    """
    Retrieve the status of an EC2 instance.

    :param instance_id: The ID of the EC2 instance
    :return: A dictionary containing the instance status or an error message
    """
    try:
        ec2 = boto3.client('ec2',
                           aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                           aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                           region_name=settings.AWS_REGION)

        response = ec2.describe_instances(InstanceIds=[instance_id])

        instance_state = response['Reservations'][0]['Instances'][0]['State']['Name']

        return {
            'success': True,
            'instance_id': instance_id,
            'status': instance_state
        }

    except ClientError as e:
        return {
            'success': False,
            'error': str(e)
        }
    except Exception as e:
        return {
            'success': False,
            'error': f"An unexpected error occurred: {str(e)}"
        }

@shared_task
def stop_instance(instance_id):
    logger.info(f"Stopping instance {instance_id}")
    try:
        ec2 = boto3.client('ec2',
                           aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                           aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                           region_name=settings.AWS_REGION)

        ec2.stop_instances(InstanceIds=[instance_id])
        logger.info(f"Instance {instance_id} stopped successfully")
    except Exception as e:
        logger.error(f"Error stopping instance {instance_id}: {e}")

def start_ec2_instance(instance_id):
    """
    Start an EC2 instance and schedule it to stop after 60 minutes.

    :param instance_id: The ID of the EC2 instance
    :return: A dictionary containing the start operation status or an error message
    """
    try:
        ec2 = boto3.client('ec2',
                           aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                           aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                           region_name=settings.AWS_REGION)

        response = ec2.start_instances(InstanceIds=[instance_id])
        current_state = response['StartingInstances'][0]['CurrentState']['Name']

        expiration_time = None

        if expiration_time is None:
            melbourne_tz = pytz.timezone('Australia/Melbourne')
            expiration_time = datetime.now(melbourne_tz) + timedelta(seconds=20)

        ec2.create_tags(Resources=[instance_id], Tags=[{'Key': 'ExpirationTime', 'Value': expiration_time.strftime('%Y-%m-%d %H:%M:%S')}])

        # Schedule the task to run in 20 seconds
        logger.info(f"Calling stop instance")
        logger.info(f"ETA: {expiration_time}")
        logger.info(f"Timezone: Australia/Melbourne")

        stop_instance.apply_async(args=[instance_id], eta=expiration_time)


        return {
            'success': True,
            'instance_id': instance_id,
            'status': current_state,
            'scheduled_stop': 'Scheduled to stop after 60 minutes'
        }

    except ClientError as e:
        return {
            'success': False,
            'error': str(e)
        }
    except Exception as e:
        return {
            'success': False,
            'error': f"An unexpected error occurred: {str(e)}"
        }