from typing import Callable, Any

from django.http import HttpRequest
from django.conf import settings
from django.contrib.auth.models import AnonymousUser

from rest_framework.response import Response

from fkdauth.jwt_auth_utils import decode_token, JWTError, JWTExpiredError

class JWTMiddleware:
    def __init__(self, get_response: Callable[..., Any]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> Response:
        
        if (auth := request.headers.get('Authorization')):
            auth_type = auth.split(' ')[0]
            if auth_type != "Bearer":
                request.jwt_user = AnonymousUser()
            else:
                token = auth.split(' ')[1]
                try:
                    request.jwt_user = decode_token(token, settings.SECRET_KEY)
                except (JWTError, JWTExpiredError):
                    request.jwt_user = AnonymousUser()
        else:
            request.jwt_user = AnonymousUser()

        response = self.get_response(request)
        return response
