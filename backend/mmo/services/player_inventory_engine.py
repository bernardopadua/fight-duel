from django.db import transaction
from django.db.models import Sum, F, Value, Window, OuterRef, Subquery
from django.db.models.functions import Coalesce
from django.forms import model_to_dict
from djangorestframework_camel_case.util import camelize

from mmo.models import Player, Item, PlayerInventory
from mmo.services.player_engine import PlayerEngine

from typing import Any

class PlayerInventoryEngine:
    @staticmethod
    def useItem(playerId: int, itemId: int) -> bool:
        if not itemId:
            return False

        iv = PlayerInventory.objects.filter(
            item_id=itemId,
            player_id=playerId
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
                    totalLife = PlayerEngine.getPlayerCalulatedLife(player)
                    if (player.player_life + item.item_power) > totalLife:
                        player.player_life = totalLife
                    else:
                        player.player_life += item.item_power
                    player.save(update_fields=["player_life"])
                elif item.item_consumable_type == Item.ItemConsumableType.STAMINA:
                    totalStamina = PlayerEngine.getPlayerCalulatedStamina(player)
                    if (player.player_stamina + item.item_power) > totalStamina:
                        player.player_stamina = totalStamina
                    else:
                        player.player_stamina += item.item_power
                    player.save(update_fields=["player_stamina"])
                
                #This is cascade.
                item.delete()
            elif item.item_type == Item.ItemType.ARMOUR:
                player.player_equipped_armour = iv
                player.save(update_fields=["player_equipped_armour"])
            elif item.item_type == Item.ItemType.WEAPON:
                player.player_equipped_weapon = iv
                player.save(update_fields=["player_equipped_weapon"])

        return True

    @staticmethod
    def lootItems(playerId: int, itemsId: list) -> bool:
        if not itemsId:
            return False

        #validanting that all items is integers ids
        for i in itemsId:
            if not isinstance(i, int):
                return False
        
        items = Item.objects.filter(
            id__in=itemsId
        ).annotate(
            totalItemsWeight=Window(expression=Sum("item_weight"))
        )

        if len(items) != len(itemsId):
            return False

        #This complication is intentional
        subPlayerInventory = (
            PlayerInventory.objects.filter(
                player_id=OuterRef('pk')
            ).exclude(
                id=OuterRef('player_equipped_weapon_id')
            ).exclude(
                id=OuterRef('player_equipped_armour_id')
            ).values(
                "player_id"
            ).annotate(
                totalItemsWeight=Sum("item__item_weight")
            ).values("totalItemsWeight")[:1]
        )

        player = Player.objects.filter(
            id=playerId
        ).annotate(
            totalItemsEquipped=(
                Coalesce(F("player_equipped_weapon__item__item_weight"), Value(0)) + 
                Coalesce(F("player_equipped_armour__item__item_weight"), Value(0))
            ),
            totalInventoryWeight=Coalesce(Subquery(subPlayerInventory), Value(0))
        ).first()
        if not player:
            return False

        totalItemsWeghtInInventory = player.totalInventoryWeight + player.totalItemsEquipped
        if ((totalItemsWeghtInInventory + items[0].totalItemsWeight)) > player.player_max_weight:
            return False

        try:
            PlayerInventory.objects.bulk_create([
                PlayerInventory(
                    item=i,
                    player=player
                ) for i in items
            ])
        except Exception as e:
            #TODO: Logging
            print(e)
            return False

        return True

    @staticmethod
    def getPlayerInventory(playerId: int) -> list[dict[str, Any]]:
        itemsInventory = PlayerInventory.objects.filter(
            player_id=playerId
        ).select_related("item").all()
        
        itemsInventoryDict = [i.item.to_dict() for i in itemsInventory]

        return itemsInventoryDict

    #TODO: Remove this.
    @staticmethod
    def testing():
        #This complication is intentional
        subPlayerInventory = (
            PlayerInventory.objects.filter(
                player_id=OuterRef('pk')
            ).exclude(
                item_id=OuterRef('player_equipped_weapon_id')
            ).exclude(
                item_id=OuterRef('player_equipped_armour_id')
            ).values(
                "player_id"
            ).annotate(
                totalItemsWeight=Sum("item__item_weight")
            ).values("totalItemsWeight")[:1]
        )

        player = Player.objects.filter(
            id=7
        ).annotate(
            totalItemsEquipped=(
                Coalesce(F("player_equipped_weapon__item__item_weight"), Value(0)) + 
                Coalesce(F("player_equipped_armour__item__item_weight"), Value(0))
            ),
            totalInventoryWeight=Coalesce(Subquery(subPlayerInventory), Value(0))
        ).first()

        print(player)