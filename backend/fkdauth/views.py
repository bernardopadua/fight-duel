from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from fkdauth.jwt_auth_utils import createToken

class LoginView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not User.objects.filter(username=username).exists():
            return Response({'error': 'User does not exist'}, status=404)

        user = authenticate(username=username, password=password)
        
        if not user:
            return Response({'error': 'Invalid credentials'}, status=401)
        else:
            token = createToken(user.id, settings.SECRET_KEY)
            return Response({'token': token}, status=200)

class RegisterUserView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({'error': 'Username and password are required'}, status=400)

        if User.objects.filter(username=username).exists():
            return Response({'error': 'User already exists'}, status=400)
        else:
            User.objects.create_user(username=username, password=make_password(password))
            return Response({'success': 'User created successfully'}, status=201)
