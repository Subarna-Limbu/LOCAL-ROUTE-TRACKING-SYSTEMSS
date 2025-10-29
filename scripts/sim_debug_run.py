import os
import django
import sys
# Ensure project root is on sys.path so Django project package is importable
proj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_transport.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from core.models import Driver, Bus, BusRoute
from django.utils import timezone

User = get_user_model()
username = 'sim_driver_for_debug'
password = 'pass1234'
user, created = User.objects.get_or_create(username=username)
if created:
    user.set_password(password)
    user.email = 'sim@example.local'
    user.save()
else:
    # Ensure password is known
    user.set_password(password)
    user.save()

# create or get driver profile
driver, dcreated = Driver.objects.get_or_create(user=user, defaults={'phone': '000', 'vehicle_number': 'SIM123', 'verified': True})
if not dcreated:
    driver.phone = '000'
    driver.vehicle_number = 'SIM123'
    driver.verified = True
    driver.save()

# create a route and bus if missing
route, rcreated = BusRoute.objects.get_or_create(name='DEBUG_ROUTE', defaults={'is_active': True})
if not rcreated:
    route.is_active = True
    route.save()

bus, bcreated = Bus.objects.get_or_create(number_plate='DEBUGBUS', defaults={'total_seats': 20, 'driver': driver, 'route': route})
if not bcreated:
    bus.driver = driver
    bus.route = route
    bus.total_seats = 20
    bus.save()

print('Using bus id:', bus.id)

c = Client()
logged_in = c.login(username=username, password=password)
print('Logged in:', logged_in)
# simulate update_location post (coordinates for Balkot approx 27.704,85.300)
debug_resp = c.get(f'/debug/bus_status/{bus.id}/')
# Instead of HTTP update, directly set bus current location and apply smoothing logic
from core.models import Stop
from django.db import transaction

# Create two stops and attach to route (pickup and later stop)
pickup_stop, _ = Stop.objects.get_or_create(name='Gatthaghar', defaults={'latitude': 27.7000, 'longitude': 85.3200})
next_stop, _ = Stop.objects.get_or_create(name='Dudhpati', defaults={'latitude': 27.7050, 'longitude': 85.3300})
try:
    # create through model RouteStop entries if not present
    if not route.routestop_set.filter(stop=pickup_stop).exists():
        route.routestop_set.create(stop=pickup_stop, order=0)
    if not route.routestop_set.filter(stop=next_stop).exists():
        route.routestop_set.create(stop=next_stop, order=1)
except Exception:
    pass

# Place bus at Balkot-like coordinates (simulated)
bus.current_lat = 27.704
bus.current_lng = 85.300
bus.save()

# Apply the smoothing logic (mirror of update_location)
import math
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

stops = route.get_stops_list()
nearest_dist_km = None
nearest_idx = None
for i, s in enumerate(stops):
    try:
        d = haversine(bus.current_lat, bus.current_lng, s.latitude, s.longitude)
        if nearest_dist_km is None or d < nearest_dist_km:
            nearest_dist_km = d
            nearest_idx = i
    except Exception:
        continue

if nearest_dist_km is not None:
    avg_speed_kmh = getattr(__import__('django.conf').conf.settings, 'AVG_SPEED_KMH', 25)
    eta_seconds = int((nearest_dist_km / avg_speed_kmh) * 3600)
    if eta_seconds < 1:
        eta_seconds = 1
    # EMA smoothing
    alpha = getattr(__import__('django.conf').conf.settings, 'ETA_SMOOTH_ALPHA', 0.3)
    prev = bus.eta_smoothed_seconds
    smoothed = eta_seconds if prev is None else (alpha * eta_seconds + (1 - alpha) * prev)
    bus.eta_seconds = eta_seconds
    bus.eta_smoothed_seconds = smoothed
    passed_thresh = getattr(__import__('django.conf').conf.settings, 'ETA_PASSED_THRESHOLD_SECONDS', 30)
    if smoothed <= passed_thresh:
        bus.eta_passed_counter = (bus.eta_passed_counter or 0) + 1
    else:
        bus.eta_passed_counter = 0
    bus.eta_updated_at = timezone.now()
    bus.save()

# fetch debug endpoint
debug_resp = c.get(f'/debug/bus_status/{bus.id}/')
print('debug endpoint status:', debug_resp.status_code)
print(debug_resp.content.decode('utf-8'))

# Also print the bus object fields from ORM to be safe
bus.refresh_from_db()
print('ORM bus fields: current_lat=', bus.current_lat, 'current_lng=', bus.current_lng, 'eta_seconds=', bus.eta_seconds, 'eta_smoothed_seconds=', bus.eta_smoothed_seconds, 'eta_passed_counter=', bus.eta_passed_counter, 'eta_updated_at=', bus.eta_updated_at)
