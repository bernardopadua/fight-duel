from django.test import TestCase
from django.contrib.auth.models import User
from django.conf import settings

from rest_framework.test import APITestCase
from rest_framework import status

from fkdauth.jwt_auth_utils import (
    create_token, decode_token, 
    JWTError, JWTExpiredError
)

class JWTTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username='test', email='test@test.com', password='123456')
        self.second_user = User.objects.create_user(username='second_user', email='second_user@test.com', password='123456')

    def test_create_token(self):
        token = create_token(self.user.id, settings.SECRET_KEY)
        token_second = create_token(self.second_user.id, settings.SECRET_KEY)
        self.assertIsNotNone(token)
        self.assertIsInstance(token, str)
        self.assertNotEqual(token, token_second)
        new_token = create_token(self.user.id, settings.SECRET_KEY, time_expires=1)
        self.assertNotEqual(token, new_token)

    def test_decode_token(self):
        import time
        token = create_token(self.user.id, settings.SECRET_KEY)
        payload = decode_token(token, settings.SECRET_KEY)
        self.assertIn('userId', payload)
        self.assertEqual(self.user.id, payload['userId'])
        
        with self.assertRaises(JWTError):
            _ = decode_token(token, "WRONG_SECRET")           

        token = create_token(self.user.id, settings.SECRET_KEY, time_expires=-1)
        with self.assertRaises(JWTExpiredError):
            _ = decode_token(token, settings.SECRET_KEY)


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