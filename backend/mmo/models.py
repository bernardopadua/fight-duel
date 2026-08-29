from typing import Any

from django.db import models
from django.contrib.auth.models import User

class World(models.Model):
    world_name = models.CharField(max_length=100)
    world_total_creatures = models.IntegerField(default=100)
    world_min_level = models.IntegerField(default=1)
    world_max_level = models.IntegerField(default=100)

class WorldCreature(models.Model):
    creature_name = models.CharField(max_length=100)
    creature_level = models.IntegerField(default=1)
    creature_life = models.IntegerField(default=100)
    creature_chance_drop = models.IntegerField(default=50)
    world = models.ForeignKey('World', on_delete=models.CASCADE)

class Item(models.Model):
    class ItemType(models.TextChoices):
        WEAPON = "weapon"
        ARMOUR = "armour"
        CONSUMABLE = "consumable"
    
    class ItemConsumableType(models.TextChoices):
        LIFE = "life"
        STAMINA = "stamina"

    item_name = models.CharField(max_length=100)
    item_power = models.IntegerField(default=0)
    item_weight = models.IntegerField(default=1)
    item_type = models.CharField(max_length=50, choices=ItemType.choices)
    item_consumable_type = models.CharField(max_length=50, choices=ItemConsumableType.choices, null=True, blank=True)
    item_created_date = models.DateTimeField(auto_now_add=True)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "itemName": self.item_name,
            "itemPower": self.item_power,
            "itemWeight": self.item_weight,
            "itemType": self.item_type,
            "itemConsumableType": self.item_consumable_type,
            "itemCreatedDate": str(self.item_created_date),
        }

class Player(models.Model):
    class PlayerStatus(models.TextChoices):
        IDLE = "idle"
        FIGHTING = "fighting"
        DEAD = "dead"

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    player_name = models.CharField(max_length=100)
    player_life = models.IntegerField(default=100)
    player_level = models.IntegerField(default=1)
    player_exp = models.IntegerField(default=0)
    player_power = models.IntegerField(default=10)
    player_stamina = models.IntegerField(default=100)
    player_equipped_weapon = models.ForeignKey('PlayerInventory', on_delete=models.SET_NULL, null=True, blank=True, related_name="player_weapon_equipped")
    player_equipped_armour = models.ForeignKey('PlayerInventory', on_delete=models.SET_NULL, null=True, blank=True, related_name="player_armour_equipped")
    player_status = models.CharField(max_length=50, choices=PlayerStatus.choices, default=PlayerStatus.IDLE)
    player_max_weight = models.IntegerField(default=100)
    player_currency = models.IntegerField(default=0)

class PlayerInventory(models.Model):
    item = models.ForeignKey('Item', on_delete=models.CASCADE)
    player = models.ForeignKey('Player', on_delete=models.CASCADE)

class Fight(models.Model):
    creature = models.ForeignKey('WorldCreature', on_delete=models.CASCADE)
    player = models.ForeignKey('Player', on_delete=models.CASCADE)
