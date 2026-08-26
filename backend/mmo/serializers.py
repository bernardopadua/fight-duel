from typing import Any

from rest_framework.serializers import ModelSerializer, ValidationError

from mmo.models import Player

class CreatePlayerSerializer(ModelSerializer):
    class Meta:
        model = Player
        fields = ['user', 'player_name', 'player_level', 'player_exp', 'player_power', 'player_stamina', 'player_equipped_weapon', 'player_equipped_armour', 'player_status', 'player_max_weight', 'player_currency']
        read_only_fields = ['user', 'player_level', 'player_exp', 'player_power', 'player_stamina', 'player_equipped_weapon', 'player_equipped_armour', 'player_status', 'player_max_weight', 'player_currency']

    def validate_player_name(self, value: str) -> str:
        if Player.objects.filter(player_name=value).exists():
            raise ValidationError('Player name already exists')
        return value
    
    @override
    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if Player.objects.filter(user=self.context['request'].user).exists():
            raise ValidationError('User already has a player')
        return attrs

class GetPlayerSerializer(ModelSerializer):
    class Meta:
        model = Player
        fields = ['user', 'player_name', 'player_level', 'player_exp', 'player_power', 'player_stamina', 'player_equipped_weapon', 'player_equipped_armour', 'player_status', 'player_max_weight', 'player_currency']
        read_only_fields = ['user', 'player_name', 'player_level', 'player_exp', 'player_power', 'player_stamina', 'player_equipped_weapon', 'player_equipped_armour', 'player_status', 'player_max_weight', 'player_currency']
