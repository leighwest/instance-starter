from dataclasses import dataclass, asdict
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .models import EC2

from .service.ec2_service import get_ec2_instance_status
from .service.ec2_service import start_ec2_instance

# FIXME: need to return this more consistently
@dataclass
class EC2DTO:
    success: bool
    instance_name: str
    status: str


@require_POST
def start_instance(request):
    instance_name = request.POST.get('instance_name')
    instance = EC2.get_by_name(request.POST.get('instance_name'))

    if instance is None:
        return JsonResponse({
            'success': False,
            'error': f"Instance with name '{instance_name}' not found."
        }, status=404)

    result = start_ec2_instance(instance.instance_id)

    response = EC2DTO(success=result.get('success'), instance_name=instance.name, status=result.get('status'))

    return JsonResponse(asdict(response), status=200 if result.get('success') else 500)

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

        if not status_response['success']:
            return JsonResponse({'success': False, 'error': status_response['error']}, status=500)

        print("in instance_status")
        print(status_response['time_remaining'])

        return JsonResponse({'success': True, 'status': status_response['status'], 'time_remaining': status_response['time_remaining']
                             })

    except:
        return JsonResponse({'success': False, 'error': 'Instance not found'}, status=404)

def starting_page(request):
    instances = EC2.objects.all()

    instances_with_status = [
        {
            'name': instance.name,
            'description': instance.description,
            'status': status_info.get('status'),
            'time_remaining': status_info.get('time_remaining')
        }
        for instance in instances
        for status_info in [get_ec2_instance_status(instance.instance_id)]
    ]

    return render(request, "ec2_starter/index.html", {
        "instances": instances_with_status
    })
