from mmo.models import Item, Player
from mmo.data.item_names import (
    ITEM_WEAPONS_NAMES, 
    ITEM_CONSUMABLE_NAMES, 
    ITEM_ARMOURS_NAMES
)

from typing import TypeAlias

import random

Currency: TypeAlias = int

class DropEngine:
    @staticmethod
    def calculate_wearable_item_power(creature_level: int) -> int:
        rng_power_level = random.choices(
            [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.2, 1.5, 3],
            weights=[60, 60, 60, 60, 60, 60, 60, 60, 60, 50, 40, 35, 5]
        )[0]
        return max(1, int(creature_level * rng_power_level))

    @staticmethod
    def calculate_consumable_item_power() -> int:
        rng_power_level = random.choices(
            [10, 15, 20, 25, 30, 40, 50, 60, 70, 80, 90, 100, 150],
            weights=[70, 70, 70, 60, 60, 55, 50, 35, 35, 25, 15, 10, 5]
        )[0]
        return max(10, int(rng_power_level))

    @staticmethod
    def calculate_wearable_item_weight() -> int:
        return random.choices(
            # Pesos:    5 (Ultra Raro), 10, 15, 20, 25, 30, 40, 50 (Comum/Pesado)
            [5, 10, 15, 20, 25, 30, 40, 50],
            weights=[5, 15, 30, 50, 60, 50, 40, 30]
        )[0]

    @classmethod
    def create_drop_item(cls, creature_level: int, *, item_type: Item.ItemType | None = None) -> Item:
        
        item_name = ""
        item_power = 0
        item_weight = 0
        item_consumable_type: str | None = None
        item_type = random.choice([
            Item.ItemType.ARMOUR,
            Item.ItemType.WEAPON,
            Item.ItemType.CONSUMABLE
        ]) if item_type is None else item_type

        if item_type == Item.ItemType.ARMOUR:
            item_name = random.choice(ITEM_ARMOURS_NAMES)
            item_power = cls.calculate_wearable_item_power(creature_level)
            item_weight = cls.calculate_wearable_item_weight()

        elif item_type == Item.ItemType.WEAPON:
            item_name = random.choice(ITEM_WEAPONS_NAMES)
            item_power = cls.calculate_wearable_item_power(creature_level)
            item_weight = cls.calculate_wearable_item_weight()

        elif item_type == Item.ItemType.CONSUMABLE:
            item_name = random.choice(ITEM_CONSUMABLE_NAMES)
            item_power = cls.calculate_consumable_item_power()
            item_consumable_type = random.choice([
                Item.ItemConsumableType.LIFE, 
                Item.ItemConsumableType.STAMINA
            ])
            item_weight = 1

        return Item.objects.create(
            item_type=item_type,
            item_name=item_name,
            item_power=item_power,
            item_weight=item_weight,
            item_consumable_type=item_consumable_type
        )

    @staticmethod
    def calculate_currency(creature_level: int) -> Currency:
        return random.randint(int(creature_level * 8), int(creature_level * 12))

    @classmethod
    def drop_items(cls, creature_level: int, creature_chance_drop: int) -> tuple[list[Item], Currency]:
        if random.randint(1, 100) > creature_chance_drop:
            return [], 0
        
        currency = 0
        if cls.calculate_chance_drop_currency(creature_level) <= creature_chance_drop:
            currency = cls.calculate_currency(creature_level)

        qty_drops = random.randint(1, 3)
        items: list[Item] = []

        for _ in range(qty_drops):
            item = cls.create_drop_item(creature_level)
            items.append(item)

        return items, currency

    @staticmethod
    def calculate_chance_drop_by_player(player: Player):
        # I will make the calculations after PVP is set.
        return random.randint(40, 100)

    @staticmethod
    def calculate_chance_drop_currency(creature_level: int) -> int:
        return random.randint(1, 100)
