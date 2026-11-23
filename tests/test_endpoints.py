import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from seeds.seed_data import seed_database

class FullSystemSmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ensure database is seeded
        seed_database()
        cls.app = create_app('development')
        cls.client = cls.app.test_client()

    def test_frontend_root_serves_html(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'JBD Travels', res.data)
        self.assertIn(b'root', res.data)

    def test_budget_planner_frontend_components(self):
        res = self.client.get('/static/js/app.js')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'isDestinationDropdownOpen', res.data)
        self.assertIn(b'filteredDestinations', res.data)
        self.assertIn(b'aria-label="Total budget in USD"', res.data)

    def test_destinations_api(self):
        res = self.client.get('/api/destinations')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertGreater(data['count'], 0)

    def test_ai_recommendations_api(self):
        res = self.client.post('/api/recommendations/destinations', json={
            'preferences': ['culture', 'sightseeing'],
            'budget': 2500,
            'duration_days': 5
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertGreater(len(data['recommendations']), 0)

    def test_itinerary_generation_api(self):
        res = self.client.post('/api/recommendations/itinerary', json={
            'destination': 'Tokyo',
            'budget': 3500,
            'duration_days': 5,
            'travelers_count': 2
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertIn('cost_breakdown', data['plan'])

    def test_flights_search_api(self):
        res = self.client.get('/api/flights/search?origin=New+York&destination=Tokyo')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertTrue(data['is_simulated'])

    def test_hotels_api(self):
        res = self.client.get('/api/hotels?partner_only=true')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertGreater(data['count'], 0)

    def test_travel_docs_check_api(self):
        res = self.client.get('/api/travel-docs/check?origin=United+States&destination=Japan')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['advisory']['destination_country'], 'Japan')

    def test_admin_dashboard_api_with_admin_token(self):
        # Login as admin
        login_res = self.client.post('/api/auth/login', json={
            'email_or_username': 'admin@jbdtravels.com',
            'password': 'Admin123!'
        })
        token = login_res.get_json()['token']

        # Access dashboard
        dash_res = self.client.get('/api/admin/dashboard', headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(dash_res.status_code, 200)
        data = dash_res.get_json()
        self.assertTrue(data['success'])
        self.assertIn('kpis', data)
        self.assertIn('charts', data)

if __name__ == '__main__':
    unittest.main()
