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
        instance = response['Reservations'][0]['Instances'][0]
        instance_state = instance['State']['Name']

        instance_time_remaining = calc_running_time_remaining(instance)

        print("in get_ec2_instance_status")
        print(instance_time_remaining)

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
            expiration_time = datetime.now(melbourne_tz) + timedelta(seconds=190)

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