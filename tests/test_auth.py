import unittest
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models import db, User

class AuthTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_customer_registration_and_login(self):
        # Register
        res = self.client.post('/api/auth/register', json={
            'username': 'john_doe',
            'email': 'john@example.com',
            'password': 'Password123!',
            'full_name': 'John Doe',
            'role': 'customer'
        })
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertIn('token', data)
        token = data['token']

        # Verify profile via /me
        res_me = self.client.get('/api/auth/me', headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(res_me.status_code, 200)
        self.assertEqual(res_me.get_json()['user']['role'], 'customer')

        # Login
        res_login = self.client.post('/api/auth/login', json={
            'email_or_username': 'john@example.com',
            'password': 'Password123!'
        })
        self.assertEqual(res_login.status_code, 200)
        self.assertTrue(res_login.get_json()['success'])

    def test_role_based_access_control(self):
        # Register customer
        res_cust = self.client.post('/api/auth/register', json={
            'username': 'normal_user',
            'email': 'user@example.com',
            'password': 'Password123!',
            'role': 'customer'
        })
        cust_token = res_cust.get_json()['token']

        # Customer trying to access admin dashboard should be denied (403)
        res_admin = self.client.get('/api/admin/dashboard', headers={'Authorization': f'Bearer {cust_token}'})
        self.assertEqual(res_admin.status_code, 403)

        # Create admin user directly (as public registration is strictly customer-only)
        admin = User(username='super_admin', email='admin@example.com', role='admin')
        admin.set_password('Password123!')
        db.session.add(admin)
        db.session.commit()

        res_login_adm = self.client.post('/api/auth/login', json={
            'email_or_username': 'super_admin',
            'password': 'Password123!'
        })
        adm_token = res_login_adm.get_json()['token']

        # Admin accessing admin dashboard should succeed (200)
        res_admin_ok = self.client.get('/api/admin/dashboard', headers={'Authorization': f'Bearer {adm_token}'})
        self.assertEqual(res_admin_ok.status_code, 200)

if __name__ == '__main__':
    unittest.main()
