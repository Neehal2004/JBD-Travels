import unittest
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models import db, User, Hotel, BookingInquiry, Itinerary, SystemSetting
from app.services.analytics_service import AnalyticsService

class AdminDashboardTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Admin user
        admin = User(username='boss', email='boss@jbdtravels.com', role='admin')
        admin.set_password('AdminPass123!')
        db.session.add(admin)
        db.session.commit()

        # Generate admin token
        res_login = self.client.post('/api/auth/login', json={
            'email_or_username': 'boss',
            'password': 'AdminPass123!'
        })
        self.admin_token = res_login.get_json()['token']
        self.headers = {'Authorization': f'Bearer {self.admin_token}'}

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_hotel_crud_operations(self):
        # 1. Create Hotel
        res_create = self.client.post('/api/admin/hotels', headers=self.headers, json={
            'name': 'Boutique Hotel Test',
            'city': 'Venice',
            'country': 'Italy',
            'address': 'Grand Canal 42',
            'stars': 4,
            'standard_rate_per_night': 250.0,
            'partner_discount_percent': 18.0,
            'jbd_commission_percent': 12.0
        })
        self.assertEqual(res_create.status_code, 201)
        hotel_data = res_create.get_json()['hotel']
        hotel_id = hotel_data['id']
        self.assertEqual(hotel_data['name'], 'Boutique Hotel Test')

        # 2. Update Hotel (rates and discount)
        res_update = self.client.put(f'/api/admin/hotels/{hotel_id}', headers=self.headers, json={
            'standard_rate_per_night': 280.0,
            'partner_discount_percent': 25.0
        })
        self.assertEqual(res_update.status_code, 200)
        updated_hotel = res_update.get_json()['hotel']
        self.assertEqual(updated_hotel['standard_rate_per_night'], 280.0)
        self.assertEqual(updated_hotel['partner_discount_percent'], 25.0)
        self.assertEqual(updated_hotel['jbd_partner_rate'], 210.0) # 280 * 0.75

        # 3. Delete Hotel
        res_delete = self.client.delete(f'/api/admin/hotels/{hotel_id}', headers=self.headers)
        self.assertEqual(res_delete.status_code, 200)
        self.assertIsNone(db.session.get(Hotel, hotel_id))

    def test_dashboard_kpis_and_charts(self):
        # Add a sample hotel and booking inquiry
        hotel = Hotel(
            name='Test Hotel', city='Sydney', country='Australia',
            address='Harbour St', stars=4, description='Harbour view',
            image_url='https://example.com/h.jpg', standard_rate_per_night=200.0,
            is_partner=True, partner_discount_percent=15.0, jbd_commission_percent=10.0
        )
        hotel.set_amenities_list(['Free Wi-Fi', 'Harbour View'])
        hotel.set_room_types_list([{'name': 'Deluxe Harbour', 'multiplier': 1.0}])
        hotel.set_nearby_attractions_list([{'name': 'Sydney Opera House', 'distance': '1 km'}])
        db.session.add(hotel)
        db.session.commit()

        summary = AnalyticsService.get_dashboard_summary()
        self.assertIn('kpis', summary)
        self.assertIn('charts', summary)
        self.assertEqual(summary['kpis']['active_partner_hotels'], 1)
        self.assertIn('monthly_trends', summary['charts'])
        self.assertIn('travel_styles', summary['charts'])

    def test_staff_governance(self):
        # 1. List users
        res_users = self.client.get('/api/admin/users', headers=self.headers)
        self.assertEqual(res_users.status_code, 200)
        self.assertGreaterEqual(res_users.get_json()['count'], 1)

        # 2. Authorize new Travel Agent
        res_create = self.client.post('/api/admin/users', headers=self.headers, json={
            'full_name': 'Sarah Connor',
            'email': 'sarah@jbdtravels.com',
            'username': 'sarah_agent',
            'password': 'AgentPassword123!',
            'role': 'employee'
        })
        self.assertEqual(res_create.status_code, 201)
        new_user = res_create.get_json()['user']
        self.assertEqual(new_user['role'], 'employee')
        user_id = new_user['id']

        # 3. Promote to Admin
        res_role = self.client.put(f'/api/admin/users/{user_id}/role', headers=self.headers, json={
            'role': 'admin'
        })
        self.assertEqual(res_role.status_code, 200)
        self.assertEqual(res_role.get_json()['user']['role'], 'admin')

if __name__ == '__main__':
    unittest.main()
