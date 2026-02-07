import logging
from datetime import datetime, timedelta

import boto3
import pytz
import redis
from asgiref.sync import async_to_sync
from botocore.exceptions import ClientError
from celery import shared_task
from channels.layers import get_channel_layer
from django.conf import settings

from instance_starter.celery import app
from .exceptions import InstanceNotFoundError, EC2ServiceError
from ..models import EC2

logger = logging.getLogger('instance_starter')
logger.propagate = True

redis_client = redis.StrictRedis.from_url(settings.CELERY_BROKER_URL)

def _get_ec2_client():
    """Get configured boto3 EC2 client."""
    return boto3.client(
        'ec2',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION
    )

def _set_global_task_id(instance_id, task_id):
    key = f"ec2_shutdown_task:{instance_id}"
    redis_client.set(key, task_id)


def _get_global_task_id(instance_id):
    key = f"ec2_shutdown_task:{instance_id}"
    return redis_client.get(key)


def _delete_global_task_id(instance_id):
    key = f"ec2_shutdown_task:{instance_id}"
    return redis_client.delete(key)


def get_ec2_instance_status(instance_id):
    """
    Retrieve the status of an EC2 instance.

    :param instance_id: The ID of the EC2 instance
    :return: A dictionary containing the instance status and time remaining
    :raises EC2ServiceError: If unable to retrieve instance status
    """
    try:
        ec2 = _get_ec2_client()

        response = ec2.describe_instances(InstanceIds=[instance_id])
        instance = response['Reservations'][0]['Instances'][0]
        instance_state = instance['State']['Name']

        instance_time_remaining = calc_running_time_remaining(instance)

        return {
            'status': instance_state,
            'time_remaining': instance_time_remaining
        }

    except ClientError as e:
        raise EC2ServiceError(f"Failed to get instance status: {str(e)}")
    except (KeyError, IndexError) as e:
        raise EC2ServiceError(f"Unexpected AWS response format: {str(e)}")
    except Exception as e:
        raise EC2ServiceError(f"An unexpected error occurred: {str(e)}")


def calc_running_time_remaining(instance):
    instance_tags = instance.get('Tags', [])
    expiration_tag = next((tag for tag in instance_tags if tag.get('Key') == 'ExpirationTime'), None)
    if expiration_tag is not None:
        expiration_str = expiration_tag['Value']
        # Parse as naive then localize to Melbourne timezone
        expiration_naive = datetime.strptime(expiration_str, '%Y-%m-%d %H:%M:%S')
        melbourne_tz = pytz.timezone('Australia/Melbourne')
        expiration_aware = melbourne_tz.localize(expiration_naive)

        # Compare timezone-aware datetimes
        now_aware = datetime.now(melbourne_tz)
        seconds_remaining = (expiration_aware - now_aware).total_seconds()
        return seconds_remaining if seconds_remaining > 0 else None
    return None


def format_ec2_update_payload(instance_name, status_data):
    instance_key = instance_name.replace(' ', '-')

    status = status_data.get('status')
    time_remaining = status_data.get('time_remaining')

    return {
        instance_key: {
            'instance_name': instance_key,
            'status': status,
            'time_remaining': time_remaining if status == "running" else None
       }
    }


@shared_task
def broadcast_ec2_instance_statuses():
    logger.info("Executing beat task")
    instances = EC2.objects.all()
    channel_layer = get_channel_layer()

    instances_data = {}
    for instance in instances:
        try:
            status_data = get_ec2_instance_status(instance.instance_id)
            instances_data.update(
                format_ec2_update_payload(instance.name, status_data)
            )
        except EC2ServiceError as e:
            logger.error(f"Failed to get status for {instance.name}: {e}")
            # Continue with other instances - don't let one failure stop broadcast

    async_to_sync(channel_layer.group_send)(
        'ec2_updates',
        {
            'type': 'ec2_update',
            'instances': instances_data
        }
    )


@shared_task
def stop_instance(instance_id, instance_name):
    logger.info(f"Stopping instance {instance_id}")
    try:
        ec2 = _get_ec2_client()

        ec2.stop_instances(InstanceIds=[instance_id])
        _delete_global_task_id(instance_id)
        logger.info(f"Successfully stopped instance {instance_id}")

    except ClientError as e:  # Be more specific
        logger.error(f"Failed to stop instance {instance_id}: {e}")
        raise EC2ServiceError(f"Failed to stop instance: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error stopping instance {instance_id}: {e}")
        raise EC2ServiceError(f"An unexpected error occurred: {str(e)}")

def start_ec2_instance(instance_name):
    """
    Start an EC2 instance and schedule it to stop after configured time.

    :param instance_name: The name of the EC2 instance
    :return: A dictionary containing the start operation status
    :raises InstanceNotFoundError: If instance doesn't exist
    :raises EC2ServiceError: If unable to start instance
    """
    instance = EC2.get_by_name(instance_name)

    # Validation
    if instance is None:
        raise InstanceNotFoundError(f"Instance '{instance_name}' not found")

    instance_id = instance.instance_id

    try:
        ec2 = _get_ec2_client()

        response = ec2.start_instances(InstanceIds=[instance_id])
        current_state = response['StartingInstances'][0]['CurrentState']['Name']

        melbourne_tz = pytz.timezone('Australia/Melbourne')
        seconds_until_shutdown = 250
        expiration_time = datetime.now(melbourne_tz) + timedelta(seconds=seconds_until_shutdown)

        ec2.create_tags(Resources=[instance_id],
                        Tags=[{'Key': 'ExpirationTime', 'Value': expiration_time.strftime('%Y-%m-%d %H:%M:%S')}])

        # Cancel any existing shutdown task
        task_id = _get_global_task_id(instance_id)
        if task_id is not None:
            app.control.revoke(task_id.decode('utf-8'), terminate=False)

        # Schedule new shutdown task
        task_result = stop_instance.apply_async(args=[instance_id, instance_name], eta=expiration_time)
        _set_global_task_id(instance_id, task_result.id)

        logger.info(f"Started instance {instance_id} ({instance_name}), scheduled to stop at {expiration_time}")

        return {
            'status': current_state,
            'instance_id': instance_id
        }

    except ClientError as e:
        raise EC2ServiceError(f"Failed to start instance: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error starting instance {instance_name}: {e}")
        raise EC2ServiceError(f"An unexpected error occurred: {str(e)}")