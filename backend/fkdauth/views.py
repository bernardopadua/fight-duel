from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.permissions import AllowAny

from fkdauth.jwt_auth_utils import create_token

class LoginView(APIView):

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        username = request.data.get("username")
        password = request.data.get("password")
        
        if not username or not password:
            return Response({"error": "Username and password are required"}, status=status.HTTP_400_BAD_REQUEST)

        if not User.objects.filter(username=username).exists():
            return Response({"error": "User does not exist"}, status=status.HTTP_404_NOT_FOUND)

        user = authenticate(username=username, password=password)
        
        if not user:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            token = create_token(user.id, settings.SECRET_KEY)
            response = Response({"token": token}, status=status.HTTP_200_OK)
            response.set_cookie("Authorization-JWT", token, httponly=True, samesite="Lax")
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
            user = User.objects.create_user(username=username, password=make_password(password))
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
