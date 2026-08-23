from typing import override

from rest_framework.generics import CreateAPIView, RetrieveAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated

from mmo.serializers import CreatePlayerSerializer, GetPlayerSerializer
from mmo.models import Player

class CreateNewPlayer(CreateAPIView):
    
    serializer_class = CreatePlayerSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class GetPlayerView(RetrieveAPIView):

    serializer_class = GetPlayerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Player.objects.filter(user=self.request.user)
        return queryset
    
    @override
    def get_object(self):
        return get_object_or_404(self.get_queryset())
