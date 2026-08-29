from django.contrib.auth.models import AnonymousUser, User
from django.conf import settings

from channels.db import database_sync_to_async

from fkdauth.jwt_auth_utils import decode_token, JWTError, JWTExpiredError

from http.cookies import SimpleCookie
import logging

logger = logging.getLogger(__name__)

class JWTASGIAuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        headers = dict(scope["headers"])
        cookie_header = headers.get(b"cookie", b"").decode()
        cookies = SimpleCookie()
        cookies.load(cookie_header)
        token = cookies.get("Authorization-JWT")

        scope["user"] = await self.get_user(token.value) if token else AnonymousUser()
        return await self.app(scope, receive, send)

    @database_sync_to_async
    def get_user(self, token):
        # decodifica JWT, busca User, retorna AnonymousUser() se inválido
        try:
            payload = decode_token(token, settings.SECRET_KEY)

            user = User.objects.filter(id=payload.get('userId', None)).first()

            if not user:
                return AnonymousUser()

            return user

        except (JWTError, JWTExpiredError):
            return AnonymousUser()
        except Exception as e:
            logger.exception("Error occurred while decoding JWT token: %s", e)
            return AnonymousUser()