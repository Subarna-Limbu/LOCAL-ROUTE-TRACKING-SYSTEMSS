# Generated migration to add ETA fields and route polyline scaffolding
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_alter_bus_route'),
    ]

    operations = [
        migrations.AddField(
            model_name='bus',
            name='eta_seconds',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='bus',
            name='eta_smoothed_seconds',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='bus',
            name='eta_passed_counter',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='bus',
            name='eta_updated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='routestop',
            name='distance_along_route_m',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='busroute',
            name='polyline',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='busroute',
            name='route_length_m',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
