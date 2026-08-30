from django.contrib.auth.models import AnonymousUser, User
from django.conf import settings
from django.core.cache import cache

from channels.db import database_sync_to_async

from fkdauth.jwt_auth_utils import decode_token, JWTError, JWTExpiredError
from fkdauth.constants import USER_JWT_BLOCKED_BEFORE

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
            payload = decode_token(token, settings.SECRET_KEY)
            user_id = payload.get('userId')
            token_iat = payload.get('iat')

            blocked_until = cache.get(USER_JWT_BLOCKED_BEFORE.format(user_id=user_id), 0)
            if blocked_until and blocked_until > token_iat:
                raise JWTError('Token revoked')

            user = User.objects.filter(id=user_id).first()

            if not user or not user.is_active:
                return AnonymousUser()

            return user

        except (JWTError, JWTExpiredError):
            return AnonymousUser()
        except Exception as e:
            logger.exception("Error occurred while decoding JWT token: %s", e)
            return AnonymousUser()