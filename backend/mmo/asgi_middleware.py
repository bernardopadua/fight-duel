from http.cookies import SimpleCookie

from django.contrib.auth.models import AnonymousUser, User
from django.conf import settings

from channels.db import database_sync_to_async

from fkdauth.jwt_auth_utils import decodeToken, JWTError, JWTExpiredError

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
            payload = decodeToken(token, settings.SECRET_KEY)

            user = User.objects.filter(id=payload.get('userId', None))

            if not user.exists():
                return AnonymousUser()

            return user.first()

        except (JWTError, JWTExpiredError):
            return AnonymousUser()
        except Exception as e:
            raise Exception(f"Invalid JWT token")