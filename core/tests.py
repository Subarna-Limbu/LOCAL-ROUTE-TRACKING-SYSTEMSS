from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from .models import Driver, Bus, BusRoute, PickupRequest


class PickupNotificationFlowTest(TestCase):
	def setUp(self):
		User = get_user_model()
		self.user = User.objects.create_user(username='passenger1', password='pass')
		self.driver_user = User.objects.create_user(username='driver1', password='pass')
		self.driver = Driver.objects.create(user=self.driver_user, phone='123', vehicle_number='V1', verified=True)
		# ensure a route exists for the bus
		self.route = BusRoute.objects.create(name='R1', is_active=True)
		self.bus = Bus.objects.create(number_plate='BUS1', total_seats=20, driver=self.driver, route=self.route)
		self.client = Client()

	def test_pickup_and_driver_notification_includes_username(self):
		# passenger sends pickup via HTTP
		self.client.login(username='passenger1', password='pass')
		resp = self.client.post('/api/send_pickup/', {'bus_id': self.bus.id, 'stop': 'balkhu', 'message': 'wait about 5 min.'})
		self.assertEqual(resp.status_code, 200)
		data = resp.json()
		self.assertEqual(data.get('status'), 'success')

		# driver fetches notifications
		self.client.login(username='driver1', password='pass')
		resp2 = self.client.get('/driver/notifications/')
		self.assertEqual(resp2.status_code, 200)
		d2 = resp2.json()
		self.assertIn('unread_count', d2)
		recent = d2.get('recent', [])
		# ensure username appears in recent payload
		self.assertTrue(any((r.get('user') == 'passenger1') for r in recent))

	def test_update_location_persists_nearest_and_passed_counter(self):
		# create route with three stops in a line
		from .models import Stop
		stop1 = Stop.objects.create(name='S1', latitude=27.0, longitude=85.0)
		stop2 = Stop.objects.create(name='S2', latitude=27.001, longitude=85.0)
		stop3 = Stop.objects.create(name='S3', latitude=27.002, longitude=85.0)
		# Because the through model requires RouteStop, add via explicit creation
		from .models import RouteStop
		RouteStop.objects.create(route=self.route, stop=stop1, order=0)
		RouteStop.objects.create(route=self.route, stop=stop2, order=1)
		RouteStop.objects.create(route=self.route, stop=stop3, order=2)

		# ensure bus exists and is attached to route
		bus = self.bus
		# simulate driver login and post location near stop1
		self.client.login(username='driver1', password='pass')
		resp = self.client.post('/api/update_location/', {'lat': '27.0000', 'lng': '85.0000'})
		self.assertEqual(resp.status_code, 200)
		bus.refresh_from_db()
		self.assertIsNotNone(bus.nearest_stop_index)
		first_idx = bus.nearest_stop_index

		# move driver forward near stop3, expect nearest_index to increase and passed counter to increment
		resp2 = self.client.post('/api/update_location/', {'lat': '27.0020', 'lng': '85.0000'})
		self.assertEqual(resp2.status_code, 200)
		bus.refresh_from_db()
		self.assertTrue(bus.nearest_stop_index >= first_idx)
		self.assertIsNotNone(bus.eta_passed_counter)

	def test_homepage_hides_passed_bus_by_nearest_index(self):
		# create small linear route
		from .models import Stop, RouteStop
		s1 = Stop.objects.create(name='H1', latitude=27.0, longitude=85.0)
		s2 = Stop.objects.create(name='H2', latitude=27.001, longitude=85.0)
		s3 = Stop.objects.create(name='H3', latitude=27.002, longitude=85.0)
		RouteStop.objects.create(route=self.route, stop=s1, order=0)
		RouteStop.objects.create(route=self.route, stop=s2, order=1)
		RouteStop.objects.create(route=self.route, stop=s3, order=2)

		# ensure a bus exists and mark its nearest_stop_index as after H2
		bus = self.bus
		bus.nearest_stop_index = 2
		bus.current_lat = 27.002
		bus.current_lng = 85.0
		bus.save()

		# request homepage with pickup H2 and destination H3 (both in route)
		resp = self.client.get('/?pickup=H2&destination=H3')
		self.assertEqual(resp.status_code, 200)
		# the template context should exist and not include the passed bus
		buses_info = resp.context.get('buses_info', [])
		# since bus is after pickup, it should be filtered out unless show_passed=1
		self.assertTrue(all(b['bus'].id != bus.id for b in buses_info))

		# when show_passed=1 the passed bus should appear
		resp2 = self.client.get('/?pickup=H2&destination=H3&show_passed=1')
		self.assertEqual(resp2.status_code, 200)
		buses_info2 = resp2.context.get('buses_info', [])
		self.assertTrue(any(b['bus'].id == bus.id for b in buses_info2))
