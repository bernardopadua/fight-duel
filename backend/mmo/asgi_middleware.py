from django.contrib.auth.models import AnonymousUser, User
from django.core.cache import cache

from channels.db import database_sync_to_async

from fkdauth.jwt_auth_utils import (
    JWTError, JWTExpiredError,
    resolve_user_and_validate_from_token
)

from mmo.constants import USER_ONE_TIME_WS_CONNECT

from http.cookies import SimpleCookie
from urllib.parse import parse_qs
import logging

logger = logging.getLogger(__name__)

class JWTASGIAuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        headers = dict(scope["headers"])
        query_params = parse_qs(scope.get('query_string', b'').decode())
        cookie_header = headers.get(b"cookie", b"").decode()
        cookies = SimpleCookie()
        cookies.load(cookie_header)

        token = cookies.get("Authorization-JWT")
        one_time_ticket = query_params.get('one-time', None)

        if one_time_ticket:
            try:
                user_id = int(await cache.aget(USER_ONE_TIME_WS_CONNECT.format(ticket=one_time_ticket[0])) or 0)
                if user_id:
                    await cache.adelete(USER_ONE_TIME_WS_CONNECT.format(ticket=one_time_ticket[0]))
                    scope["user"] = await self.get_user_one_time(user_id)
                else:
                    scope["user"] = AnonymousUser()
            except Exception as e:
                logger.exception("Error occurred while decoding one-time ticket: %s", e)
                scope["user"] = AnonymousUser()
        elif token:
            scope["user"] = await self.get_user(token.value)
        else:
            scope["user"] = AnonymousUser()
        
        return await self.app(scope, receive, send)

    @database_sync_to_async    
    def get_user_one_time(self, user_id: int) -> User | AnonymousUser:
        try:
            user = User.objects.filter(id=user_id).first()
            if not user or not user.is_active:
                return AnonymousUser()

            return user
        except Exception as e:
            logger.exception('Error occurred while getting user from one-time ticket: %s', e)
            return AnonymousUser()

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