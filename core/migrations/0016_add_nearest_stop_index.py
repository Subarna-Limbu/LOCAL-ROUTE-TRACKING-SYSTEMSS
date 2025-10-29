"""Add nearest_stop_index field to Bus

Revision ID: 0016_add_nearest_stop_index
Revises: 0015_add_eta_and_routepolyline
Create Date: 2025-10-24 00:00
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_add_eta_and_routepolyline'),
    ]

    operations = [
        migrations.AddField(
            model_name='bus',
            name='nearest_stop_index',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
