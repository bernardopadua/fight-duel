from django.conf import settings
from django.http import HttpRequest
from django.contrib.auth.models import User

from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from django.core.cache import cache

from fkdauth.constants import USER_JWT_BLOCKED_BEFORE

from fkdauth.jwt_auth_utils import (
    decode_token, JWTError, JWTExpiredError,
    get_token_from_request
)

from typing import override
import logging

logger = logging.getLogger(__name__)

class JWTAuthenticationBackend(BaseAuthentication):
    @override
    def authenticate(self, request: HttpRequest) -> tuple[User, str] | None:
        token = ''
       
        try:
            if not (token := get_token_from_request(request)):
                return None

            payload = decode_token(token, settings.SECRET_KEY)

            user_id = payload['userId']
            token_iat = payload['iat']

            blocked_until = cache.get(USER_JWT_BLOCKED_BEFORE.format(user_id=user_id), 0)
            if blocked_until and blocked_until > token_iat:
                raise JWTError('Token revoked')

            user = User.objects.filter(id=user_id).first()
            if not user:
                return None

            return (user, token)

        except (JWTError, JWTExpiredError) as e:
            logger.warning('JWT Error: %s, for request from %s', str(e), request.META.get("REMOTE_ADDR", "Unknown"))
            raise AuthenticationFailed(f"Invalid JWT token")
        except Exception as e:
            logger.error('Invalid JWT token: %s, for request from %s', str(e), request.META.get("REMOTE_ADDR", "Unknown"))
            raise AuthenticationFailed(f"Invalid JWT token")
    
    @override
    def authenticate_header(self, request: HttpRequest) -> str:
        return 'Bearer'
            