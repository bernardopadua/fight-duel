from django.test import override_settings
from django.contrib.auth.models import User
from django.test import TransactionTestCase
from django.conf import settings

from unittest.mock import patch

from mmo.services.fight_engine import FightEngine
from mmo.models import Fight, Player, World, WorldCreature, Item

from fkdauth.jwt_auth_utils import create_token

import threading

@override_settings(
    CHANNEL_LAYERS={"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}},
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "race-conditions-tests"
        }
    }
)
class FightLockRaceConditionTests(TransactionTestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username='test', email='test@test.com', password='123456')
        self.user_2 = User.objects.create_user(username='test_2', email='test_2@test.com', password='123456')
        self.user_3 = User.objects.create_user(username='test_3', email='test_3@test.com', password='123456')

        self.token = create_token(self.user.id, settings.SECRET_KEY)
        self.token_2 = create_token(self.user_2.id, settings.SECRET_KEY)
        self.token_3 = create_token(self.user_3.id, settings.SECRET_KEY)

        self.world = World.objects.create(
            world_name='TestWorld',
            world_total_creatures=2,
            world_min_level=1,
            world_max_level=10
        )

        self.world_2 = World.objects.create(
            world_name='TestWorld2',
            world_total_creatures=2,
            world_min_level=10,
            world_max_level=20
        )

        self.player_life = 100
        self.player_power = 10
        self.player = Player.objects.create(
            player_name='TestPlayer',
            player_level=10,
            player_power=10,
            player_life=self.player_life,
            user=self.user,
            player_world=self.world
        )

        self.player_2_power = 10
        self.player_2 = Player.objects.create(
            player_name='TestPlayer2',
            player_level=10,
            player_power=self.player_2_power,
            player_life=self.player_life,
            user=self.user_2,
            player_world=self.world
        )

        self.player_3_power = 10
        self.player_3 = Player.objects.create(
            player_name='TestPlayer3',
            player_level=10,
            player_power=self.player_3_power,
            player_life=self.player_life,
            user=self.user_3,
            player_world=self.world
        )
        
        self.creature_name = 'TestCreature'
        self.creature_level = 1
        self.creature_life = 100
        self.creature = WorldCreature.objects.create(
            world=self.world,
            creature_name=self.creature_name,
            creature_level=self.creature_level,
            creature_life=self.creature_life,
            creature_chance_drop=0
        )

        self.item_name_life_potion = 'TestItem'
        self.item_type_life_potion = Item.ItemType.CONSUMABLE
        self.item_power_life_potion = 100
        self.item_weight_life_potion = 10
        self.item_life_potion = Item.objects.create(
            item_name=self.item_name_life_potion,
            item_type=self.item_type_life_potion,
            item_power=self.item_power_life_potion,
            item_weight=self.item_weight_life_potion,
            item_consumable_type=Item.ItemConsumableType.LIFE
        )

        self.item_name_armour = 'TestArmour'
        self.item_type_armour = Item.ItemType.ARMOUR
        self.item_power_armour = 10
        self.item_weight_armour = 10
        self.item_armour = Item.objects.create(
            item_name=self.item_name_armour,
            item_type=self.item_type_armour,
            item_power=self.item_power_armour,
            item_weight=self.item_weight_armour
        )

        self.item_name_armour_2 = 'TestArmour2'
        self.item_type_armour_2 = Item.ItemType.ARMOUR
        self.item_power_armour_2 = 10
        self.item_weight_armour_2 = 10
        self.item_armour_2 = Item.objects.create(
            item_name=self.item_name_armour_2,
            item_type=self.item_type_armour_2,
            item_power=self.item_power_armour_2,
            item_weight=self.item_weight_armour_2
        )

        self.item_name_weapon = 'TestWeapon'
        self.item_type_weapon = Item.ItemType.WEAPON
        self.item_power_weapon = 10
        self.item_weight_weapon = 10
        self.item_weapon = Item.objects.create(
            item_name=self.item_name_weapon,
            item_type=self.item_type_weapon,
            item_power=self.item_power_weapon,
            item_weight=self.item_weight_weapon
        )

    def test_double_move_player_fight_creation_clean(self):
        barrier = threading.Barrier(2)
        results = []

        def lock_fight(creature_id):
            try:
                barrier.wait()
                f = FightEngine.lock_fight(self.player.id, creature_id=creature_id)
                if f:
                    results.append(f)
            finally:
                from django.db import connection
                connection.close()

        t1 = threading.Thread(target=lock_fight, args=(self.creature.id,))
        t2 = threading.Thread(target=lock_fight, args=(self.creature.id,))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        active_fights = Fight.objects.all()
        self.assertEqual(active_fights.count(), 1)
        self.assertEqual(len(results), 1)

        fight = active_fights.first()
        self.assertIsNotNone(fight)
        self.assertEqual(fight.creature.id, self.creature.id)
        self.assertEqual(fight.player.id, self.player.id)

    def test_mutual_pvp_selection_same_time_race_condition(self):
        barrier = threading.Barrier(2)
        results = []
        def player_1_locks():
            try:
                barrier.wait()  
                fight = FightEngine.lock_fight(
                    self.player.id, 
                    opponent_id=self.player_2.id
                )
                if fight:
                    results.append(('p1', fight))
            finally:
                from django.db import connection
                connection.close()
        def player_2_locks():
            try:
                barrier.wait()
                fight = FightEngine.lock_fight(
                    self.player_2.id, 
                    opponent_id=self.player.id
                )
                if fight:
                    results.append(('p2', fight))
            finally:
                from django.db import connection
                connection.close()
                
        t1 = threading.Thread(target=player_1_locks)
        t2 = threading.Thread(target=player_2_locks)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        active_fights = Fight.objects.all()
        self.assertEqual(active_fights.count(), 1)
        self.assertEqual(len(results), 1)

        fight = active_fights.first()

        self.assertIsNotNone(fight)
        self.assertEqual({fight.player_id, fight.opponent_id}, {self.player.id, self.player_2.id})

