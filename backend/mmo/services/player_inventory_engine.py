from asgiref.sync import async_to_sync

from channels.layers import get_channel_layer

from django.core.cache import cache
from django.db import transaction
from django.db.models import Sum, F, Value, Window, OuterRef, Subquery
from django.db.models.functions import Coalesce, Least

from mmo.models import Player, Item, PlayerInventory
from mmo.services.player_engine import PlayerEngine
from mmo.services.drop_engine import DropEngine
from mmo.constants import USER_CHANNEL_WS_LOGGED

from typing import Any
import logging

logger = logging.getLogger(__name__)

class PlayerInventoryEngine:
    @staticmethod
    def use_item(player_id: int, item_id: int) -> bool:
        if not item_id:
            return False

        iv = PlayerInventory.objects.filter(
            item_id=item_id,
            player_id=player_id
        ).select_related(
            "item",
            "player"
        ).first()
        if not iv:
            return False
        
        item: Item = iv.item
        player: Player = iv.player
        with transaction.atomic():
            if item.item_type == Item.ItemType.CONSUMABLE:
                if item.item_consumable_type == Item.ItemConsumableType.LIFE:
                    Player.objects.filter(
                        id=player_id
                    ).update(
                        player_life=Least(F('player_life')+item.item_power, F('player_max_life'))
                    )
                elif item.item_consumable_type == Item.ItemConsumableType.STAMINA:
                    Player.objects.filter(
                        id=player_id
                    ).update(
                        player_stamina=Least(F('player_stamina')+item.item_power, F('player_max_stamina'))
                    )
                
                #This is cascade.
                item.delete()
            elif item.item_type == Item.ItemType.ARMOUR:
                player.player_equipped_armour = iv
                Player.objects.filter(
                    id=player_id
                ).update(
                    player_equipped_armour=iv,
                    player_max_life=PlayerEngine.get_player_calculated_life(player)
                )
            elif item.item_type == Item.ItemType.WEAPON:
                player.player_equipped_weapon = iv
                Player.objects.filter(
                    id=player_id
                ).update(
                    player_equipped_weapon=iv,
                    player_max_life=PlayerEngine.get_player_calculated_life(player)
                )

        return True

    @staticmethod
    def salvage_item(player_id: int, user_id: int, inventory_id: int) -> None:
        with transaction.atomic():
            iv = PlayerInventory.objects.select_for_update(
                of=['self'],
                skip_locked=True
            ).filter(
                id=inventory_id,
                player_id=player_id
            ).select_related(
                'item',
                'player'
            ).first()
            if not iv:
                logger.warning("Inventory item %s not found for player %s", inventory_id, player_id)
                return

            item: Item = iv.item
            player: Player = iv.player
            currency = DropEngine.calculate_currency_from_salvage(
                item.item_power, item.item_weight,
                is_consumable=item.item_type == Item.ItemType.CONSUMABLE
            )
            if iv.id == player.player_equipped_armour_id or iv.id == player.player_equipped_weapon_id:
                if iv.id == player.player_equipped_weapon_id:
                    player.player_equipped_weapon = None
                if iv.id == player.player_equipped_armour_id:
                    player.player_equipped_armour = None
                player.player_max_life = PlayerEngine.get_player_calculated_life(player)
                Player.objects.filter(
                    id=player_id
                ).update(
                    player_currency=F('player_currency') + currency,
                    player_max_life=player.player_max_life
                )
            else:
                Player.objects.filter(
                    id=player_id
                ).update(
                    player_currency=F('player_currency') + currency
                )

            iv.delete()

            def notify_player():
                channel_user = cache.get(
                    USER_CHANNEL_WS_LOGGED.format(user_id=user_id)
                )
                cl = get_channel_layer()
                if not cl or not channel_user:
                    return

                async_to_sync(cl.send)(channel_user, {
                    'type': 'player.earned.currency',
                    'data': {
                        'currency': currency
                    }
                })
            transaction.on_commit(notify_player)

    @staticmethod
    def loot_items(player_id: int, items_ids: list[int]) -> bool:
        if not items_ids:
            return False

        #validanting that all items is integers ids
        for i in items_ids:
            if not isinstance(i, int):
                return False
        
        items = Item.objects.filter(
            id__in=items_ids
        ).annotate(
            total_items_weight=Window(expression=Sum("item_weight"))
        )

        if len(items) != len(items_ids):
            return False

        #This complication is intentional
        sub_player_inventory = (
            PlayerInventory.objects.filter(
                player_id=OuterRef('pk')
            ).exclude(
                id=Coalesce(OuterRef('player_equipped_weapon_id'), Value(0))
            ).exclude(
                id=Coalesce(OuterRef('player_equipped_armour_id'), Value(0))
            ).values(
                "player_id"
            ).annotate(
                total_items_weight=Sum("item__item_weight")
            ).values("total_items_weight")[:1]
        )

        #query to debug eventually
        player_query = Player.objects.filter(
            id=player_id
        ).annotate(
            total_items_equipped=(
                Coalesce(F("player_equipped_weapon__item__item_weight"), Value(0)) + 
                Coalesce(F("player_equipped_armour__item__item_weight"), Value(0))
            ),
            total_inventory_weight=Coalesce(Subquery(sub_player_inventory), Value(0))
        )
        player = player_query.first()
        if not player:
            return False

        total_items_weight_in_inventory = player.total_inventory_weight + player.total_items_equipped
        if ((total_items_weight_in_inventory + items[0].total_items_weight)) > player.player_max_weight:
            return False

        try:
            PlayerInventory.objects.bulk_create([
                PlayerInventory(
                    item=i,
                    player=player
                ) for i in items
            ])
        except Exception as e:
            logger.error(f"Error loding items {items_ids} for player {player_id}: {e}", exc_info=True)
            return False

        return True

    @staticmethod
    def get_player_inventory(player_id: int) -> list[dict[str, Any]]:
        items_inventory = PlayerInventory.objects.filter(
            player_id=player_id
        ).select_related('item').all()

        items_inventory_dict = [i.item.to_dict() for i in items_inventory]

        return items_inventory_dict
