from django.urls import path

from . import views

urlpatterns = [
    path("", views.starting_page, name="starting-page"),

    path('start_instance/', views.start_instance, name='start-instance')
]
