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
                    total_life = PlayerEngine.get_player_calculated_life(player)
                    if (player.player_life + item.item_power) > total_life:
                        player.player_life = total_life
                    else:
                        player.player_life += item.item_power
                    player.save(update_fields=["player_life"])
                elif item.item_consumable_type == Item.ItemConsumableType.STAMINA:
                    total_stamina = PlayerEngine.get_player_calculated_stamina(player)
                    if (player.player_stamina + item.item_power) > total_stamina:
                        player.player_stamina = total_stamina
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
                id=OuterRef('player_equipped_weapon_id')
            ).exclude(
                id=OuterRef('player_equipped_armour_id')
            ).values(
                "player_id"
            ).annotate(
                total_items_weight=Sum("item__item_weight")
            ).values("total_items_weight")[:1]
        )

        player = Player.objects.filter(
            id=player_id
        ).annotate(
            total_items_equipped=(
                Coalesce(F("player_equipped_weapon__item__item_weight"), Value(0)) + 
                Coalesce(F("player_equipped_armour__item__item_weight"), Value(0))
            ),
            total_inventory_weight=Coalesce(Subquery(sub_player_inventory), Value(0))
        ).first()
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
            #TODO: Logging
            print(e)
            return False

        return True

    @staticmethod
    def get_player_inventory(player_id: int) -> list[dict[str, Any]]:
        items_inventory = PlayerInventory.objects.filter(
            player_id=player_id
        ).select_related("item").all()
        
        items_inventory_dict = [i.item.to_dict() for i in items_inventory]

        return items_inventory_dict

    #TODO: Remove this.
    @staticmethod
    def testing() -> None:
        #This complication is intentional
        sub_player_inventory = (
            PlayerInventory.objects.filter(
                player_id=OuterRef('pk')
            ).exclude(
                item_id=OuterRef('player_equipped_weapon_id')
            ).exclude(
                item_id=OuterRef('player_equipped_armour_id')
            ).values(
                "player_id"
            ).annotate(
                total_items_weight=Sum("item__item_weight")
            ).values("total_items_weight")[:1]
        )

        player = Player.objects.filter(
            id=7
        ).annotate(
            total_items_equipped=(
                Coalesce(F("player_equipped_weapon__item__item_weight"), Value(0)) + 
                Coalesce(F("player_equipped_armour__item__item_weight"), Value(0))
            ),
            total_inventory_weight=Coalesce(Subquery(sub_player_inventory), Value(0))
        ).first()

        print(player)