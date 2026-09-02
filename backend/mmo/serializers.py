from typing import Any

from rest_framework.serializers import (
    ModelSerializer, ValidationError,
    SerializerMethodField
)

from mmo.models import Player, World

from typing import override

class CreatePlayerSerializer(ModelSerializer):
    class Meta:
        model = Player
        fields = ['id', 'user', 'player_name', 'player_level', 'player_exp', 'player_power', 'player_stamina', 'player_equipped_weapon', 'player_equipped_armour', 'player_status', 'player_max_weight', 'player_currency']
        read_only_fields = ['id', 'user', 'player_level', 'player_exp', 'player_power', 'player_stamina', 'player_equipped_weapon', 'player_equipped_armour', 'player_status', 'player_max_weight', 'player_currency']

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
    player_equipped_weapon_item = SerializerMethodField()
    player_equipped_armour_item = SerializerMethodField()
    
    class Meta:
        model = Player
        fields = [
            'user', 'player_name', 'player_level', 'player_exp', 
            'player_power', 'player_stamina', 'player_max_stamina', 
            'player_equipped_weapon', 'player_equipped_weapon_item',
            'player_equipped_armour', 'player_equipped_armour_item',
            'player_status', 'player_max_weight', 
            'player_currency', 'player_life','player_max_life'
        ]
        read_only_fields = [
            'user', 'player_name', 'player_level', 'player_exp', 
            'player_power', 'player_stamina', 'player_max_stamina', 
            'player_equipped_weapon', 'player_equipped_weapon_item',
            'player_equipped_armour', 'player_equipped_armour_item',
            'player_status', 'player_max_weight', 
            'player_currency', 'player_life','player_max_life'
        ]
    
    def get_player_equipped_weapon_item(self, obj: Player) -> dict[str, Any] | None:
        if obj.player_equipped_weapon is None:
            return None
        return {
            "item_name": obj.player_equipped_weapon.item.item_name,
            "item_power": obj.player_equipped_weapon.item.item_power,
            "item_weight": obj.player_equipped_weapon.item.item_weight
        }

    def get_player_equipped_armour_item(self, obj: Player) -> dict[str, Any] | None:
        if obj.player_equipped_armour is None:
            return None
        return {
            "item_name": obj.player_equipped_armour.item.item_name,
            "item_power": obj.player_equipped_armour.item.item_power,
            "item_weight": obj.player_equipped_armour.item.item_weight
        }

class GetWorldSerializer(ModelSerializer):
    class Meta:
        model = World
        fields = [
            'id', 'world_name', 
            'world_min_level', 'world_max_level'
        ]
        read_only_fields = [
            'id', 'world_name', 'world_min_level', 
            'world_max_level'
        ]