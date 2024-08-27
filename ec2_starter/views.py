from django.shortcuts import render

from .models import Ec2

from .service.ec2_service import get_ec2_instance_status


def starting_page(request):

    instances = Ec2.objects.all()

    instances_with_status = [
        {
            'name': instance.name,
            'description': instance.description,
            'status': get_ec2_instance_status(instance.instance_id).get('status')
        }
        for instance in instances
    ]
    return render(request, "ec2_starter/index.html", {
        "instances": instances_with_status
    })
