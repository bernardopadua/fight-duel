from django.urls import path
from .views import CreateNewPlayer, GetPlayerView


urlpatterns = [
    path('create/player/', CreateNewPlayer.as_view(), name='create_player'),
    path('player/', GetPlayerView.as_view(), name='get_player')
]
