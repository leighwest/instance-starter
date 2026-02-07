from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .models import EC2
from .service.ec2_service import get_ec2_instance_status, start_ec2_instance
from .service.exceptions import InstanceNotFoundError, EC2ServiceError

import logging
logger = logging.getLogger('instance_starter')
logger.propagate = True

@require_POST
def start_instance(request):
    instance_name = request.POST.get('instance_name')

    try:
        result = start_ec2_instance(instance_name)

        return JsonResponse({
            'success': True,
            'instance_name': instance_name,
            'status': result['status']
        }, status=202)

    except InstanceNotFoundError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=404)
    except EC2ServiceError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def instance_status(request):
    """
    Endpoint to fetch the current status of an EC2 instance.
    """
    instance_name = request.GET.get('instance_name')

    if not instance_name:
        return JsonResponse({'success': False, 'error': 'Missing instance_name'}, status=400)

    try:
        instance = EC2.objects.get(name=instance_name)
        status_response = get_ec2_instance_status(instance.instance_id)

        return JsonResponse({
            'success': True,
            'status': status_response['status'],
            'time_remaining': status_response['time_remaining']
        })

    except EC2.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Instance not found'}, status=404)
    except EC2ServiceError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

def starting_page(request):
    instances = EC2.objects.all()

    instances_with_status = []
    for instance in instances:
        try:
            status_info = get_ec2_instance_status(instance.instance_id)
            instances_with_status.append({
                'name': instance.name,
                'description': instance.description,
                'status': status_info.get('status'),
                'time_remaining': status_info.get('time_remaining')
            })
        except EC2ServiceError as e:
            # If AWS call fails, show unknown - WebSocket will retry
            instances_with_status.append({
                'name': instance.name,
                'description': instance.description,
                'status': 'unknown',
                'time_remaining': None
            })
            logger.error(f"Failed to get status for {instance.name}: {e}")

    return render(request, "ec2_starter/index.html", {
        "instances": instances_with_status
    })
