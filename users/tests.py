from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

User = get_user_model()


class AuthTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@school.com',
            username='test@school.com',
            first_name='Test',
            last_name='User',
            password='testpass123',
            role='admin',
        )

    def test_login_success(self):
        res = self.client.post(
            '/api/v1/auth/login/',
            {'email': 'test@school.com', 'password': 'testpass123'},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('access', res.data)
        self.assertIn('refresh', res.data)
        self.assertIn('user', res.data)

    def test_login_wrong_password(self):
        res = self.client.post(
            '/api/v1/auth/login/',
            {'email': 'test@school.com', 'password': 'wrongpass'},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_missing_credentials(self):
        res = self.client.post('/api/v1/auth/login/', {}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_profile_requires_auth(self):
        res = self.client.get('/api/v1/auth/profile/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_with_auth(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.get('/api/v1/auth/profile/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['email'], 'test@school.com')

    def test_student_list_requires_auth(self):
        res = self.client.get('/api/v1/users/students/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
