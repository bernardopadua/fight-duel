from django.urls import path
from .views import CreateNewPlayer, GetPlayerView, GetWorldView


urlpatterns = [
    path('create/player/', CreateNewPlayer.as_view(), name='create_player'),
    path('player/', GetPlayerView.as_view(), name='get_player'),
    path('worlds/', GetWorldView.as_view(), name='get_worlds')
]
