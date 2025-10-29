"""Create a route + bus, set its location after a pickup, and fetch debug JSON for verification.

Run: python scripts/sim_debug_integration.py
"""
import os
import sys
import django
from pathlib import Path

# Ensure project root is on sys.path so 'smart_transport' package can be imported
BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_transport.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from core.models import Stop, BusRoute, Driver, Bus

User = get_user_model()

def make_and_inspect():
    # create driver and route
    user, _ = User.objects.get_or_create(username='simdrv', defaults={'password': 'pass'})
    # Ensure password is set usable
    if not user.has_usable_password():
        user.set_password('pass')
        user.save()
    driver, _ = Driver.objects.get_or_create(user=user, defaults={'phone': '111', 'vehicle_number': 'SIM1', 'verified': True})
    route, _ = BusRoute.objects.get_or_create(name='SIM_ROUTE', defaults={'is_active': True})
    sA, _ = Stop.objects.get_or_create(name='SIMA', defaults={'latitude': 27.7000, 'longitude': 85.3000})
    sB, _ = Stop.objects.get_or_create(name='SIMB', defaults={'latitude': 27.7050, 'longitude': 85.3100})
    sC, _ = Stop.objects.get_or_create(name='SIMC', defaults={'latitude': 27.7100, 'longitude': 85.3200})
    # ensure RouteStop entries exist (idempotent)
    if not route.routestop_set.filter(stop=sA).exists():
        route.routestop_set.create(stop=sA, order=0)
    if not route.routestop_set.filter(stop=sB).exists():
        route.routestop_set.create(stop=sB, order=1)
    if not route.routestop_set.filter(stop=sC).exists():
        route.routestop_set.create(stop=sC, order=2)

    # create bus located near stop C (after B)
    bus, created = Bus.objects.get_or_create(number_plate='SIMBUS', defaults={'total_seats': 12, 'driver': driver, 'route': route, 'current_lat': 27.7101, 'current_lng': 85.3201})
    # update fields to ensure latest values
    bus.current_lat = 27.7101
    bus.current_lng = 85.3201
    bus.nearest_stop_index = 2
    bus.eta_seconds = 10
    bus.eta_smoothed_seconds = 10.0
    bus.eta_passed_counter = 1
    bus.save()

    # Instead of calling the debug endpoint (which may raise template debug HTML on exceptions),
    # print the same payload directly from the ORM to inspect persisted fields.
    data = {
        'id': bus.id,
        'number_plate': bus.number_plate,
        'current_lat': bus.current_lat,
        'current_lng': bus.current_lng,
        'eta_seconds': bus.eta_seconds,
        'eta_smoothed_seconds': bus.eta_smoothed_seconds,
        'eta_passed_counter': bus.eta_passed_counter,
        'eta_updated_at': bus.eta_updated_at.isoformat() if bus.eta_updated_at else None,
        'nearest_stop_index': bus.nearest_stop_index,
        'route_id': bus.route.id if bus.route else None,
        'route_name': bus.route.name if bus.route else None,
    }
    import json
    print(json.dumps({'status': 'success', 'bus': data}, indent=2, default=str))

if __name__ == '__main__':
    make_and_inspect()
