from typing import override

from django.conf import settings
from django.contrib.auth.models import User

from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from fkdauth.jwt_auth_utils import decodeToken, JWTError, JWTExpiredError

class JWTAuthenticationBackend(BaseAuthentication):
    @override
    def authenticate(self, request):
        
        auth_header = get_authorization_header(request).split()
        if not auth_header or len(auth_header) < 2:
            return None
        
        try:
            authType = auth_header[0]
            if authType != b'Bearer':
                return None

            token = auth_header[1].decode()
            payload = decodeToken(token, settings.SECRET_KEY)

            user = User.objects.filter(id=payload.get('userId', None))

            if not user.exists():
                return None

            return (user.first(), token)

        except (JWTError, JWTExpiredError):
            return None
        except Exception as e:
            raise AuthenticationFailed(f"Invalid JWT token: {e}")

        return None
    
    @override
    def authenticate_header(self, request):
        return 'Bearer'
            