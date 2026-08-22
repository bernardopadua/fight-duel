from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated

from mmo.serializers import CreatePlayerSerializer, GetPlayerSerializer
from mmo.models import Player

class CreateNewPlayer(CreateAPIView):
    
    serializer_class = CreatePlayerSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class GetPlayerView(ListAPIView):

    serializer_class = GetPlayerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Player.objects.filter(user=self.request.user)
        return queryset