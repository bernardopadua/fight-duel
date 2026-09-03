from django.http import HttpRequest
from django.contrib.auth.models import User

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from fkdauth.jwt_auth_utils import (
    JWTError, JWTExpiredError,
    get_token_from_request,
    resolve_user_and_validate_from_token
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

            user = resolve_user_and_validate_from_token(token)
            if not user or not user.is_active:
                return None

            return (user, token)

        except (JWTError, JWTExpiredError) as e:
            logger.warning('JWT Error: %s, for request from %s', str(e), request.META.get("REMOTE_ADDR", "Unknown"))
            return None
        except Exception as e:
            logger.error('Invalid JWT token: %s, for request from %s', str(e), request.META.get("REMOTE_ADDR", "Unknown"))
            raise AuthenticationFailed(f"Invalid JWT token")
    
    @override
    def authenticate_header(self, request: HttpRequest) -> str:
        return 'Bearer'
            