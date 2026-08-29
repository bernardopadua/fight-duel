from typing import override

from django.conf import settings
from django.http import HttpRequest
from django.contrib.auth.models import User

from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from fkdauth.jwt_auth_utils import decode_token, JWTError, JWTExpiredError

class JWTAuthenticationBackend(BaseAuthentication):
    @override
    def authenticate(self, request: HttpRequest) -> tuple[User, str] | None:
        
        auth_header = get_authorization_header(request).split()
        if not auth_header or len(auth_header) < 2:
            return None
        
        try:
            token = ''

            auth_type = auth_header[0]
            if auth_type != b'Bearer':
                return None

            token = auth_header[1].decode()
            payload = decode_token(token, settings.SECRET_KEY)

            user = User.objects.filter(id=payload.get('userId', None)).first()

            if not user:
                return None

            return (user, token)

        except (JWTError, JWTExpiredError):
            return None
        except Exception as e:
            raise AuthenticationFailed(f"Invalid JWT token: {e}")
    
    @override
    def authenticate_header(self, request: HttpRequest) -> str:
        return 'Bearer'
            