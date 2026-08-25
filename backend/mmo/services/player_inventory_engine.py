from django.db import transaction
from django.db.models import Sum, F, Value, Window, OuterRef, Subquery
from django.db.models.functions import Coalesce
from django.forms import model_to_dict

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
            if item.itemType == Item.ItemType.CONSUMABLE:
                if item.itemConsumableType == Item.ItemConsumableType.LIFE:
                    totalLife = PlayerEngine.getPlayerCalulatedLife(player)
                    if (player.playerLife+item.itemPower) > totalLife:
                        player.playerLife = totalLife
                    else:
                        player.playerLife += item.itemPower
                    player.save(update_fields=["playerLife"])
                elif item.itemConsumableType == Item.ItemConsumableType.STAMINA:
                    totalStamina = PlayerEngine.getPlayerCalulatedStamina(player)
                    if (player.playerStamina+item.itemPower) > totalStamina:
                        player.playerStamina = totalStamina
                    else:
                        player.playerStamina += item.itemPower
                    player.save(update_fields=["playerStamina"])
                
                #This is cascade.
                item.delete()
            elif item.itemType == Item.ItemType.ARMOUR:
                player.playerEquipedArmour = iv
                player.save(update_fields=["playerEquipedArmour"])
            elif item.itemType == Item.ItemType.WEAPON:
                player.playerEquipedWeapon = iv
                player.save(update_fields=["playerEquipedWeapon"])

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
            totalItemsWeight=Window(expression=Sum("itemWeight"))
        )

        if len(items) != len(itemsId):
            return False

        #This complication is intentional
        subPlayerInventory = (
            PlayerInventory.objects.filter(
                player_id=OuterRef('pk')
            ).exclude(
                id=OuterRef('playerEquipedWeapon_id')
            ).exclude(
                id=OuterRef('playerEquipedArmour_id')
            ).values(
                "player_id"
            ).annotate(
                totalItemsWeight=Sum("item__itemWeight")
            ).values("totalItemsWeight")[:1]
        )

        player = Player.objects.filter(
            id=playerId
        ).annotate(
            totalItemsEquipped=(
                Coalesce(F("playerEquipedWeapon__item__itemWeight"), Value(0)) + 
                Coalesce(F("playerEquipedArmour__item__itemWeight"), Value(0))
            ),
            totalInventoryWeight=Coalesce(Subquery(subPlayerInventory), Value(0))
        ).first()
        if not player:
            return False

        totalItemsWeghtInInventory = player.totalInventoryWeight + player.totalItemsEquipped
        if ((totalItemsWeghtInInventory + items[0].totalItemsWeight)) > player.playerMaxWeight:
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
        
        itemsInventoryDict = [model_to_dict(i.item) for i in itemsInventory]

        return itemsInventoryDict

    #TODO: Remove this.
    @staticmethod
    def testing():
        #This complication is intentional
        subPlayerInventory = (
            PlayerInventory.objects.filter(
                player_id=OuterRef('pk')
            ).exclude(
                item_id=OuterRef('playerEquipedWeapon_id')
            ).exclude(
                item_id=OuterRef('playerEquipedArmour_id')
            ).values(
                "player_id"
            ).annotate(
                totalItemsWeight=Sum("item__itemWeight")
            ).values("totalItemsWeight")[:1]
        )

        player = Player.objects.filter(
            id=7
        ).annotate(
            totalItemsEquipped=(
                Coalesce(F("playerEquipedWeapon__itemWeight"), Value(0)) + 
                Coalesce(F("playerEquipedArmour__itemWeight"), Value(0))
            ),
            totalInventoryWeight=Coalesce(Subquery(subPlayerInventory), Value(0))
        ).first()

        print(player)