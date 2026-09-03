from django.contrib.auth.models import AnonymousUser, User

from channels.db import database_sync_to_async

from fkdauth.jwt_auth_utils import (
    JWTError, JWTExpiredError,
    resolve_user_and_validate_from_token
)

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
    def get_user(self, token: str) -> User | AnonymousUser:
        try:
            user = resolve_user_and_validate_from_token(token)
            if not user or not user.is_active:
                return AnonymousUser()

            return user

        except (JWTError, JWTExpiredError):
            return AnonymousUser()
        except Exception as e:
            logger.exception("Error occurred while decoding JWT token: %s", e)
            return AnonymousUser()