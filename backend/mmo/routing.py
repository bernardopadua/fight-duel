from django.urls import re_path, path
from mmo.consumers import FkingDuelConsumer

websocket_urlpatterns = [
    #re_path(r"ws/fight/(?P<fight_id>\w+)/$", FightConsumer.as_asgi()),
    path("ws/fight/", FkingDuelConsumer.as_asgi()),
]