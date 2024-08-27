import boto3
from django.conf import settings
from botocore.exceptions import ClientError


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
