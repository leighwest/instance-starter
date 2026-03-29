from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('ec2_starter', '0003_ec2_description'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ec2',
            name='state',
        ),
        migrations.RemoveField(
            model_name='ec2',
            name='last_start_time',
        ),
    ]