from django.db.models import QuerySet

from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated

from mmo.serializers import (
    CreatePlayerSerializer, 
    GetPlayerSerializer, 
    GetWorldSerializer
)
from mmo.models import Player, World

from typing import override

class CreateNewPlayer(CreateAPIView):
    
    serializer_class = CreatePlayerSerializer
    permission_classes = [IsAuthenticated]
    
    @override
    def perform_create(self, serializer: CreatePlayerSerializer) -> None:
        serializer.save(user=self.request.user)

class GetPlayerView(RetrieveAPIView):

    serializer_class = GetPlayerSerializer
    permission_classes = [IsAuthenticated]

    @override
    def get_queryset(self) -> QuerySet[Player]:
        queryset = Player.objects.select_related(
            'player_equipped_weapon__item',
            'player_equipped_armour__item',
            'player_world'
        ).filter(user=self.request.user)
        return queryset

    @override
    def get_object(self) -> Player:
        return get_object_or_404(self.get_queryset())

class GetWorldView(ListAPIView):

    serializer_class = GetWorldSerializer
    permission_classes = [IsAuthenticated]

    @override
    def get_queryset(self) -> QuerySet[Player]:
        queryset = World.objects.all()
        return queryset
    