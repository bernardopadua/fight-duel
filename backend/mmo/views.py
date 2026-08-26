from django.db.models import QuerySet

from rest_framework.generics import CreateAPIView, RetrieveAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated

from mmo.serializers import CreatePlayerSerializer, GetPlayerSerializer
from mmo.models import Player

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
        queryset = Player.objects.filter(user=self.request.user)
        return queryset
    
    @override
    def get_object(self) -> Player:
        return get_object_or_404(self.get_queryset())
