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
# simulate update_location post (coordinates for Balkot: approx 27.7179,85.2797) - adjust slightly
resp = c.post('/api/update_location/', {'lat': '27.7179', 'lng': '85.2797'})
print('update_location response status:', resp.status_code)
print('update_location response content:', resp.content)

# fetch debug endpoint
debug_resp = c.get(f'/debug/bus_status/{bus.id}/')
print('debug endpoint status:', debug_resp.status_code)
print(debug_resp.content)

# Also print the bus object fields from ORM to be safe
bus.refresh_from_db()
print('ORM bus fields: current_lat=', bus.current_lat, 'current_lng=', bus.current_lng, 'eta_seconds=', bus.eta_seconds, 'eta_smoothed_seconds=', bus.eta_smoothed_seconds, 'eta_passed_counter=', bus.eta_passed_counter, 'eta_updated_at=', bus.eta_updated_at)
