from mmo.models import Item
from mmo.data.item_names import (
    ITEM_WEAPONS_NAMES, 
    ITEM_CONSUMABLE_NAMES, 
    ITEM_ARMOURS_NAMES
)

import random

class DropEngine:
    @staticmethod
    def calculateWearableItemPower(creatureLevel: int) -> int:
        rngPowerLevel = random.choices(
            [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.2, 1.5, 3],
            weights=[60, 60, 60, 60, 60, 60, 60, 60, 60, 50, 40, 35, 5]
        )[0]
        return max(1, int(creatureLevel*rngPowerLevel))

    @staticmethod
    def calculateConsumableItemPower() -> int:
        rngPowerLevel = random.choices(
            [10, 15, 20, 25, 30, 40, 50, 60, 70, 80, 90, 100, 150],
            weights=[70, 70, 70, 60, 60, 55, 50, 35, 35, 25, 15, 10, 5]
        )[0]
        return max(10, int(rngPowerLevel))

    @staticmethod
    def calculateWearableItemWeight() -> int:
        return random.choices(
            # Pesos:    5 (Ultra Raro), 10, 15, 20, 25, 30, 40, 50 (Comum/Pesado)
            [5, 10, 15, 20, 25, 30, 40, 50],
            weights=[5, 15, 30, 50, 60, 50, 40, 30]
        )[0]

    @classmethod
    def createDropItem(cls, creatureLevel: int) -> Item:
        
        itemName = ""
        itemPower = 0
        itemWeight = 0
        itemConsumableType: str | None = None
        itemType = random.choice([
            Item.ItemType.ARMOUR,
            Item.ItemType.WEAPON,
            Item.ItemType.CONSUMABLE
        ])

        if itemType == Item.ItemType.ARMOUR:
            itemName = random.choice(ITEM_ARMOURS_NAMES)
            itemPower = cls.calculateWearableItemPower(creatureLevel)
            itemWeight = cls.calculateWearableItemWeight()

        elif itemType == Item.ItemType.WEAPON:
            itemName = random.choice(ITEM_WEAPONS_NAMES)
            itemPower = cls.calculateWearableItemPower(creatureLevel)
            itemWeight = cls.calculateWearableItemWeight()

        elif itemType == Item.ItemType.CONSUMABLE:
            itemName = random.choice(ITEM_CONSUMABLE_NAMES)
            itemPower = cls.calculateConsumableItemPower()
            itemConsumableType = random.choice([
                Item.ItemConsumableType.LIFE, 
                Item.ItemConsumableType.STAMINA
            ])
            itemWeight = 1

        return Item.objects.create(
            itemType=itemType,
            itemName=itemName,
            itemPower=itemPower,
            itemWeight=itemWeight,
            itemConsumableType=itemConsumableType
        )
    
    @classmethod
    def dropItems(cls, creatureLevel: int, creatureChanceDrop: int) -> list[Item]:
        if random.randint(1, 100) > creatureChanceDrop:
            return []
        
        qtyDrops = random.randint(1, 3)
        items: list[Item] = []

        for _ in range(qtyDrops):
            item = cls.createDropItem(creatureLevel)
            items.append(item)

        return items            