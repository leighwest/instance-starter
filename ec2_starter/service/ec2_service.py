import boto3
import pytz
import redis
from datetime import datetime, timedelta

from celery import shared_task

from django.conf import settings
from botocore.exceptions import ClientError

import logging

from instance_starter.celery import app

logger = logging.getLogger('instance_starter')
logger.propagate = True

redis_client = redis.StrictRedis.from_url(settings.CELERY_BROKER_URL)

def set_global_task_id(instance_id, task_id):
    key = f"ec2_shutdown_task:{instance_id}"
    redis_client.set(key, task_id)


def get_global_task_id(instance_id):
    key = f"ec2_shutdown_task:{instance_id}"
    return redis_client.get(key)


def delete_global_task_id(instance_id):
    key = f"ec2_shutdown_task:{instance_id}"
    return redis_client.delete(key)


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
        instance = response['Reservations'][0]['Instances'][0]
        instance_state = instance['State']['Name']

        instance_time_remaining = calc_running_time_remaining(instance)

        return {
            'success': True,
            'instance_id': instance_id,
            'status': instance_state,
            'time_remaining': instance_time_remaining
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


def calc_running_time_remaining(instance):
    instance_tags = instance.get('Tags', [])
    expiration_tag = next((tag for tag in instance_tags if tag.get('Key') == 'ExpirationTime'), None)
    if expiration_tag is not None:
        expiration_str = expiration_tag['Value']
        expiration_date = datetime.strptime(expiration_str, '%Y-%m-%d %H:%M:%S')
        seconds_remaining = (expiration_date - datetime.now()).total_seconds()
        return seconds_remaining if seconds_remaining > 0 else None

    return None


@shared_task
def stop_instance(instance_id):
    logger.info(f"Stopping instance {instance_id}")
    try:
        ec2 = boto3.client('ec2',
                           aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                           aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                           region_name=settings.AWS_REGION)

        ec2.stop_instances(InstanceIds=[instance_id])
        delete_global_task_id(instance_id)
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
            expiration_time = datetime.now(melbourne_tz) + timedelta(seconds=70)

        ec2.create_tags(Resources=[instance_id],
                        Tags=[{'Key': 'ExpirationTime', 'Value': expiration_time.strftime('%Y-%m-%d %H:%M:%S')}])

        task_id = get_global_task_id(instance_id)
        if task_id is not None:
            app.control.revoke(task_id.decode('utf-8'), terminate=False)

        task_result = stop_instance.apply_async(args=[instance_id], eta=expiration_time)
        set_global_task_id(instance_id, task_result.id)

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