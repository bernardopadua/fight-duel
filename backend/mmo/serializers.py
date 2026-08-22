from typing import Any

from rest_framework.serializers import ModelSerializer, ValidationError

from mmo.models import Player

class CreatePlayerSerializer(ModelSerializer):

    class Meta:
        model = Player
        fields = ['user', 'playerName', 'playerLevel', 'playerExp', 'playerPower', 'playerStamina', 'playerEquipedWeapon', 'playerEquipedArmour', 'playerStatus', 'playerMaxWeight', 'playerCurrency']
        read_only_fields = ['user', 'playerLevel', 'playerExp', 'playerPower', 'playerStamina', 'playerEquipedWeapon', 'playerEquipedArmour', 'playerStatus', 'playerMaxWeight', 'playerCurrency']

    def validate_playerName(self, value: str):
        if Player.objects.filter(playerName=value).exists():
            raise ValidationError('Player name already exists')
        return value
    
    def validate(self, attrs: dict[str, Any]):
        if Player.objects.filter(user=self.context['request'].user).exists():
            raise ValidationError('User already has a player')
        return attrs

class GetPlayerSerializer(ModelSerializer):
    class Meta:
        model = Player
        fields = ['user', 'playerName', 'playerLevel', 'playerExp', 'playerPower', 'playerStamina', 'playerEquipedWeapon', 'playerEquipedArmour', 'playerStatus', 'playerMaxWeight', 'playerCurrency']
        read_only_fields = ['user', 'playerName', 'playerLevel', 'playerExp', 'playerPower', 'playerStamina', 'playerEquipedWeapon', 'playerEquipedArmour', 'playerStatus', 'playerMaxWeight', 'playerCurrency']
