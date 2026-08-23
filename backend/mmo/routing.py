from django.urls import re_path
from mmo.consumers import FightConsumer

websocket_urlpatterns = [
    re_path(r"ws/fight/(?P<fight_id>\w+)/$", FightConsumer.as_asgi()),
]