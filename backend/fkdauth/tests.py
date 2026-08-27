from django.contrib.auth.models import User

from rest_framework.test import APITestCase
from rest_framework import status

class UserRegistrationTest(APITestCase):
    def test_user_registration(self):
        response = self.client.post(
            '/api/auth/register/', 
            {'username': 'test', 'email': 'test@test.com', 'password': '123456'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("Authorization-JWT", response.cookies)
        self.assertIn("token", response.data)
        self.assertEqual(response.data['user']['username'], 'test')
    
    def test_user_registration_duplicate_username(self):
        response = self.client.post(
            '/api/auth/register/', 
            {'username': 'test', 'email': 'test@test.com', 'password': '123456'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.post(
            '/api/auth/register/', 
            {'username': 'test', 'email': 'test@test.com', 'password': '123456'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        

    def test_user_registration_missing_password(self):
        response = self.client.post(
            '/api/auth/register/', 
            {'username': 'test', 'email': 'test@test.com'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

class UserLoginTest(APITestCase):
    def test_user_login(self):
        User.objects.create_user(username='test', email='test@test.com', password='123456')
        
        response = self.client.post(
            '/api/auth/login/', 
            {'username': 'test', 'password': '123456'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Authorization-JWT", response.cookies)
        self.assertIn("token", response.data)

    def test_user_login_wrong_credentials(self):
        User.objects.create_user(username='test', email='test@test.com', password='123456')

        response = self.client.post(
            '/api/auth/login/', 
            {'username': 'test', 'password': 'wrongpassword'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error", response.data)

    def test_user_login_missing_password(self):
        response = self.client.post(
            '/api/auth/login/', 
            {'username': 'test'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_user_login_missing_username(self):
        response = self.client.post(
            '/api/auth/login/', 
            {'password': '123456'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)