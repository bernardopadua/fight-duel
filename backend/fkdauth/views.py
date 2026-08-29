from django.conf import settings
from django.core.cache import cache
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User

from django.middleware.csrf import get_token
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import AuthenticationFailed

from fkdauth.jwt_auth_utils import create_token, get_expiration_from_request
from fkdauth.constants import USER_JWT_BLOCKED_BEFORE

import time

class LoginView(APIView):

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        username = request.data.get("username")
        password = request.data.get("password")
        
        if not username or not password:
            return Response({"error": "Username and password are required"}, status=status.HTTP_400_BAD_REQUEST)

        if not User.objects.filter(username=username).exists():
            return Response({'error': 'User does not exist'}, status=status.HTTP_404_NOT_FOUND)

        user = authenticate(username=username, password=password)
        
        if not user:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            token = create_token(user.id, settings.SECRET_KEY)
            response = Response({'token': token}, status=status.HTTP_200_OK)
            response.set_cookie('Authorization-JWT', token, httponly=True, samesite='Lax')
            return response

class HealthCheck(APIView):
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request: Request) -> Response:
        return Response({'status': 'ok'}, status=status.HTTP_200_OK)

class LogoutView(APIView):
    
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        response = Response({'success': True}, status=status.HTTP_200_OK)
        
        expiration = get_expiration_from_request(request)
        if not expiration:
            raise AuthenticationFailed('Invalid JWT token')

        cache.set(
            USER_JWT_BLOCKED_BEFORE.format(user_id=request.user.id), 
            time.time(),
            timeout=max(expiration - time.time(), 1)
        )
        response.delete_cookie('Authorization-JWT')
        return response

class RegisterUserView(APIView):

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response({"error": "Username and password are required"}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({"error": "User already exists"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            user = User.objects.create_user(username=username, password=password)
            token = create_token(user.id, settings.SECRET_KEY)
            response = Response({
                "success": True, 
                "token": token,
                "user": {
                    "username": user.username
                }
            }, status=status.HTTP_201_CREATED)
            response.set_cookie("Authorization-JWT", token, httponly=True, samesite="Lax")
            return response
