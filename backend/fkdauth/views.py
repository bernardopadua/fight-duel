from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

from rest_framework.views import APIView
from rest_framework.response import Response

from fkdauth.jwt_auth_utils import createToken

class LoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if (user := User.objects.filter(username=username)) and user.exists():
            return Response({'error': 'User does not exist'}, status=404)

        user = authenticate(username=username, password=password)
        
        if not user:
            return Response({'error': 'Invalid credentials'}, status=401)
        else:
            token = createToken(user.id, settings.SECRET_KEY)
            return Response({'token': token}, status=200)

class RegisterUserView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if User.objects.filter(username=username).exists():
            return Response({'error': 'User already exists'}, status=400)
        else:
            User.objects.create_user(username=username, password=password)
            return Response({'success': 'User created successfully'}, status=201)
