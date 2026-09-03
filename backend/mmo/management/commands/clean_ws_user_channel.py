from django.core.management.base import BaseCommand
from django.core.cache import cache

from mmo.constants import USER_CHANNEL_WS_LOGGED

class Command(BaseCommand):
    help = "Removes the channel of every user connected via websocket."

    def handle(self, *args, **kwargs):
        redis = cache._cache.get_client(write=True)
        keys = redis.scan_iter(
            cache.make_key(USER_CHANNEL_WS_LOGGED.format(user_id="*"))
        )
        for key in keys:
            redis.unlink(key)

