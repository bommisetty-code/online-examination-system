import unittest

from app import create_app


class ApiFlowTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()

    def test_health_endpoint(self):
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['status'], 'ok')

    def test_admin_can_create_student_account(self):
        admin = self.client.post('/api/auth/register', json={
            'email': 'admin@example.com',
            'username': 'admincreate',
            'password': 'Password1',
            'full_name': 'Admin Account',
            'role': 'admin'
        })
        self.assertEqual(admin.status_code, 201)

        login = self.client.post('/api/auth/login', json={
            'username': 'admincreate',
            'password': 'Password1'
        })
        token = login.get_json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}

        create_student = self.client.post('/api/admin/students', json={
            'email': 'student2@example.com',
            'username': 'student2',
            'password': 'Password1',
            'full_name': 'Created Student'
        }, headers=headers)

        self.assertEqual(create_student.status_code, 201)
        payload = create_student.get_json()
        self.assertEqual(payload['user']['role'], 'student')
        self.assertEqual(payload['user']['username'], 'student2')


if __name__ == '__main__':
    unittest.main()
