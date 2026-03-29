from django.contrib import admin
from .models import EC2

@admin.register(EC2)
class EC2Admin(admin.ModelAdmin):
    list_display = ('name', 'instance_id', 'region', 'description')
    search_fields = ('name', 'instance_id')