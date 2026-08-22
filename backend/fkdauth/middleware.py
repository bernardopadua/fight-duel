from typing import Callable, Any

from django.http import HttpRequest
from django.conf import settings
from django.contrib.auth.models import AnonymousUser

from rest_framework.response import Response

from jwt_auth_utils import decodeToken, JWTError, JWTExpiredError

class JWTMiddleware:
    def __init__(self, get_response: Callable[..., Any]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> Response:
        
        if (auth := request.headers.get('Authorization')):
            authType = auth.split(' ')[0]
            if authType != "Bearer":
                request.jwtUser = AnonymousUser()
            else:
                token = auth.split(' ')[1]
                try:
                    request.jwtUser = decodeToken(token, settings.SECRET_KEY)
                except (JWTError, JWTExpiredError):
                    request.jwtUser = AnonymousUser()
        else:
            request.jwtUser = AnonymousUser()

        response = self.get_response(request)
        return response
