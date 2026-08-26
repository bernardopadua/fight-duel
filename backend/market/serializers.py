from typing import Any

from rest_framework.serializers import (
    ModelSerializer, ValidationError,
    ReadOnlyField
)

from mmo.models import Item, PlayerInventory
from market.models import MarketDeal

class MarketDealSerializer(ModelSerializer):
    player_name = ReadOnlyField(source='player.player_name')
    player_level = ReadOnlyField(source='player.player_level')
    item_power = ReadOnlyField(source='item.item_power')

    class Meta:
        model = MarketDeal
        fields = [
            'id', 'item', 'player', 'player_name', 'player_level',
             'market_currency_amount', 'market_created_date', 'item_power'
        ]
        read_only_fields = [
            'id', 'player', 'player_name', 
            'player_level', 'market_created_date', 
            'item_power'
        ]

    def validate_item(self, value: Item):
        check_item = PlayerInventory.objects.filter(
            item=value,
            player__user=self.context['request'].user
        )
        if not check_item.exists():
            raise ValidationError('Item is not in the player\'s inventory.')

        check_market_deals = MarketDeal.objects.filter(
            item=value
        )
        if self.instance:
            check_market_deals = check_market_deals.exclude(
                id=self.instance.id
            )
        if check_market_deals.exists():
            raise ValidationError('Item is already in the market.')

        return value

    def validate_market_currency_amount(self, value: int):
        if value <= 0:
            raise ValidationError('Value cannot be 0 or less than 0')
        
        return value