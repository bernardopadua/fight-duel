from django.db import models
from django.contrib.auth.models import User

class World(models.Model):
    worldName = models.CharField(max_length=100)
    worldTotalCreatures = models.IntegerField(default=100)
    worldMinLevel = models.IntegerField(default=1)
    worldMaxLevel = models.IntegerField(default=0)

class WorldCreature(models.Model):
    creatureName = models.CharField(max_length=100)
    creatureLevel = models.IntegerField(default=1)
    creatureLife = models.IntegerField(default=100)
    creatureChanceDrop = models.IntegerField(default=50)

class Item(models.Model):
    itemName = models.CharField(max_length=100)
    itemPower = models.IntegerField(default=0)
    itemWeight = models.IntegerField(default=1)

class Player(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    playerName = models.CharField(max_length=100)
    playerLife = models.IntegerField(default=100)
    playerLevel = models.IntegerField(default=1)
    playerExp = models.IntegerField(default=0)
    playerPower = models.IntegerField(default=1)
    playerStamina = models.IntegerField(default=100)
    playerEquipedWeapon = models.ForeignKey('Item', on_delete=models.SET_NULL, null=True, blank=True, related_name="player_weapon_equipped")
    playerEquipedArmour = models.ForeignKey('Item', on_delete=models.SET_NULL, null=True, blank=True, related_name="player_armour_equipped")
    playerStatus = models.CharField(max_length=50, default='idle') #idle, fighting, running, dead
    playerMaxWeight = models.IntegerField(default=100)
    playerCurrency = models.IntegerField(default=0)

class PlayerInventory(models.Model):
    item = models.ForeignKey('Item', on_delete=models.CASCADE)
    player = models.ForeignKey('Player', on_delete=models.CASCADE)

class Fight(models.Model):
    creature = models.ForeignKey('WorldCreature', on_delete=models.CASCADE)
    player = models.ForeignKey('Player', on_delete=models.CASCADE)
