from django.shortcuts import render

def starting_page(request):
    return render(request, "ec2_starter/index.html")