from django.shortcuts import render

from .models import Ec2


def starting_page(request):
    instances = Ec2.objects.all()
    return render(request, "ec2_starter/index.html", {
        "instances": instances
    })
