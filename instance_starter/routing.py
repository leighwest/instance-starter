from django.urls import path

from ec2_starter import consumers

websocket_urlpatterns = [
    path('ws/ec2_updates/', consumers.EC2Consumer.as_asgi()),
]